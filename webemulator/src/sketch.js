import { WebMidi, Note } from 'webmidi';


const LHIN_PORT = "LHIN";
const LHOUT_PORT = "LHOUT";

const NUM_LASERS = 11
const LASER_OFFSET = 5
const LASER_TILT = 5

const LASER_OFF_BRIGHTNESS = 32;
const LASER_ON_BRIGHTNESS = 127;

const CURSOR_SIZE = 35;
const CURSOR_MIN_Y = 100;

const COLOR_DARK = "#030712";
const COLOR_LIGHT = "#f9fafb";
const COLOR_BEAM = "#ff2056";

const MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]; // map step -> note
const MAJOR_SCALE_INVERSE = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]; // map note -> step


export default (p) => {
  class ViewTransform {
    constructor() {
      this.tx = 0;
      this.ty = 0;
      this.zoom = 0;
    }

    update() {
      this.tx = p.windowWidth * 0.5;
      this.ty = p.windowHeight * 0.9;
      this.zoom = Math.min(p.windowWidth / 400, p.windowHeight / 800);
    }

    transform() {
      p.translate(viewTransform.tx, viewTransform.ty);
      p.scale(viewTransform.zoom, -viewTransform.zoom);
    }

    apply(x, y) {
      return [
        x * this.zoom + this.tx,
        y * -this.zoom + this.ty,
      ];
    }

    applyInverse(x, y) {
      return [
        (x - this.tx) / this.zoom,
        (y - this.ty) / -this.zoom,
      ];
    }
  }

  class Laser {
    constructor(x, tilt) {
      this.x = x;
      this.m = Math.atan(tilt * Math.PI / 180);

      this.intersection = Infinity;
      this.hoverIntersection = Infinity;
      this.brightness = LASER_OFF_BRIGHTNESS;

      this.intersectionPrev = Infinity; // used to compute modulation
      this.intersectionDuration = 0;
    }
  }


  const currentScale = {
    key: 0, // 0..11
    octave: 5, // 0..10
    mode: 0, // 0..6
  };

  let viewTransform = null;
  let lasers = null;

  let midiIn = null;
  let midiOut = null;

  let previousPitchBend = 0;
  let previousVelocities = new Uint8Array(128).fill(0);
  let noteLookupTable = new Int8Array(NUM_LASERS).fill(-1); // map step/laser index -> note
  let noteLookupTableReverse = new Int8Array(128).fill(-1); // map note -> step/laser index

  let brightnessLookupCache = new Int8Array(128).fill(-1);
  let emulatedLookupCache = new Int8Array(128).fill(-1);

  let messageConsole = Array(8).fill(null).map(() => "");


  const lookupLaserIndex = (note, on, cache) => {
    if (on) {
      // lookup via table
      const index = noteLookupTableReverse[note];
      cache[note] = index;
      return index;
    } else {
      let index = cache[note];
      if (index === -1) {
        // use normal reverse lookup if no cache entry exists
        index = noteLookupTableReverse[note];
      }
      cache[note] = -1;
      return index;
    }
  };

  const updateLookupTables = () => {
    // reset tables
    noteLookupTable = new Int8Array(NUM_LASERS).fill(-1);
    noteLookupTableReverse = new Int8Array(128).fill(-1);

    // generate scale table
    const scaleTable = Array(7).fill(0).map((_, i) => (MAJOR_SCALE[(i - MAJOR_SCALE_INVERSE[currentScale.key] + 7) % 7] + currentScale.key + 12) % 12);

    for (let i = 0; i < NUM_LASERS; i++) {
      // use major scale and root note to convert from laser index to midi note number
      const step = currentScale.mode + i;
      const octave = parseInt(step / scaleTable.length);
      const stepWithinOctave = step % scaleTable.length;
      const note = (currentScale.octave + octave) * 12 + scaleTable[stepWithinOctave];
      console.log(`${i} -> ${(new Note(note)).name}${(new Note(note)).accidental || ""} (${note})`);

      // skip if note is out of bounds
      if (note < 0 || note >= 128) {
        continue;
      }

      // store both forward and reverse lookup
      noteLookupTable[i] = note;
      noteLookupTableReverse[note] = i;
    }
  };

  const updateOutput = () => {
    let velocities = new Uint8Array(128).fill(0);

    let modulationContributorCount = 0;
    let modulationSum = 0;

    for (let [i, laser] of lasers.entries()) {
      // reset intersection duration
      if (laser.intersection === Infinity) {
        laser.intersectionDuration = 0;
      }

      // convert laser index to note number
      const note = noteLookupTable[i];
      if (note === -1) {
        continue;
      }

      // set the note
      if (laser.intersection !== Infinity) {
        velocities[note] = 127;
        laser.intersectionDuration += 1;

        // update pitch bend
        const modulationDelay = 10; // time (in ticks) after which the modulation becomes effective
        const modulationGain = 0.05; // amount of modulation
        const durationFactor = Math.tanh(laser.intersectionDuration - modulationDelay) * 0.5 + 0.5;
        const modulation = Math.tanh((laser.intersection - laser.intersectionPrev) * modulationGain) * durationFactor;
        modulationContributorCount += 1;
        modulationSum += modulation;
        laser.intersectionPrev = laser.intersection;
      }
    }

    // compare to previous state and send any changed notes
    for (let note = 0; note < 128; note++) {
      const previousVelocity = previousVelocities[note];
      const velocity = velocities[note];

      // send note off
      if (velocity === 0 && previousVelocity > 0) {
        midiOut.channels[1].sendNoteOff(note, { rawAttack: 0 });
      }

      // send note on
      if (velocity > 0 && previousVelocity === 0) {
        midiOut.channels[1].sendNoteOn(note, { rawAttack: velocity });
      }
    }

    // store previous velocities
    previousVelocities = velocities;

    // send pitch bend
    let pitchBend = 0;
    if (modulationContributorCount > 0 && Math.abs(modulationSum) > 0.01) {
      pitchBend = modulationSum / modulationContributorCount;
    }

    if (pitchBend !== previousPitchBend) {
      midiOut.channels[1].sendPitchBend(pitchBend);
    }
    previousPitchBend = pitchBend;
  };

  const updateIntersections = () => {
    const [mx, my] = viewTransform.applyInverse(p.mouseX, p.mouseY);
    for (let laser of lasers) {
      // calculate distance to laser
      const d = Math.abs(mx - laser.m * my - laser.x) / Math.sqrt(1 + laser.m * laser.m); // point to line distance

      // if close enough, set the hover intersection
      if (my > CURSOR_MIN_Y && d < CURSOR_SIZE / 2) {
        laser.hoverIntersection = my;
      } else {
        laser.hoverIntersection = Infinity;
      }

      // set actual intersection when the mouse is pressed
      if (p.mouseIsPressed) {
        laser.intersection = laser.hoverIntersection;
      } else {
        laser.intersection = Infinity;
      }
    }
  };

  const onMidiIn = (event) => {
    messageConsole.shift();
    messageConsole.push(`ch=${event.message.channel} cmd=${event.message.command} d1=${event.message.dataBytes[0]} d2=${event.message.dataBytes[1]}`);

    const NOTE_OFF = 8;
    const NOTE_ON = 9;

    const channel = event.message.channel;

    switch (event.message.command) {
      case NOTE_OFF:
      case NOTE_ON: {
        const note = event.message.dataBytes[0];
        const velocity = event.message.command === NOTE_ON ? event.message.dataBytes[1] : 0;

        switch (event.message.channel) {
          case 1: {
            // lookup laser index
            const laserIndex = lookupLaserIndex(note, velocity > 0, brightnessLookupCache);
            if (laserIndex === -1) {
              return;
            }

            // set the laser brightness
            const brightness = p.constrain(velocity, LASER_OFF_BRIGHTNESS, LASER_ON_BRIGHTNESS);
            lasers[laserIndex].brightness = brightness;

            break;
          }
          case 2: {
            if (velocity === 0) {
              break;
            }

            // reset
            if (note === 127) {
              currentScale.key = 0;
              currentScale.octave = 5;
              currentScale.mode = 0;
              // updateLookupTables() is called below

              previousVelocities = new Uint8Array(128).fill(0);
              brightnessLookupCache = new Int8Array(128).fill(-1);
              emulatedLookupCache = new Int8Array(128).fill(-1);

              midiOut.sendAllSoundOff();
            }

            // set key
            if (note >= 0 && note < 12) {
              currentScale.key = note;
            }

            // set mode
            if (note >= 12 && note < 24) {
              for (let [i, step] of MAJOR_SCALE.entries()) {
                if (note - 12 === step) {
                  currentScale.mode = i;
                }
              }
            }

            // set octave
            if (note >= 24 && note < 34) {
              currentScale.octave = note - 24;
            }

            // TODO: do this from the update loop whenever scale settings changed
            updateLookupTables();

            break;
          }
          case 3: {
            // lookup laser index
            const laserIndex = lookupLaserIndex(note, velocity > 0, emulatedLookupCache);
            if (laserIndex === -1) {
              return;
            }

            // emulate intersection
            lasers[laserIndex].intersection = velocity > 0 ? Math.min(500, (velocity * 10)) : Infinity;

            break;
          }
          default:
            break;
        }
        break;
      }
      default:
        break;
    }
  };

  const onWebMidiEnabled = () => {
    // check for input and output
    midiIn = WebMidi.getInputByName(LHIN_PORT);
    midiOut = WebMidi.getOutputByName(LHOUT_PORT);

    midiIn.addListener("midimessage", onMidiIn);
    midiOut.sendAllSoundOff();
  };

  p.setup = () => {
    p.createCanvas(p.windowWidth, p.windowHeight);

    // initialize lookup tables
    updateLookupTables();

    // initialize global instances
    viewTransform = new ViewTransform();
    lasers = Array(NUM_LASERS)
      .fill(null)
      .map((_, i) => (i - (NUM_LASERS - 1) / 2))
      .map((x) => new Laser(x * LASER_OFFSET, x * LASER_TILT));

    // setup webmidi
    WebMidi
      .enable()
      .then(onWebMidiEnabled)
      .catch((err) => console.error('WebMidi could not be enabled.', err));

    // main update loop
    setInterval(() => updateOutput(), 1000 / 50);
  };

  p.draw = () => {
    p.background(COLOR_DARK);

    // calculate and apply view transform
    viewTransform.update();

    p.push();
    viewTransform.transform();

    // draw the laserharp enclosure
    p.fill(COLOR_DARK);
    p.stroke(COLOR_LIGHT);
    p.strokeWeight(1.0);

    p.rect(-100, -35, 200, 35);
    p.line(-65, -2, -65, -35 + 2);
    p.line(65, -2, 65, -35 + 2);

    // draw all laser beams
    const colorBeam = p.color(COLOR_BEAM);

    for (let laser of lasers) {
      const y0 = 2;
      const x0 = laser.x + laser.m * y0;
      const y1 = viewTransform.applyInverse(0, -1)[1]; // overlap by one pixel so there's no visible seam
      const x1 = laser.x + laser.m * y1;

      // draw laser beam
      p.push();
      colorBeam.setAlpha(laser.brightness * 255 / 127);
      p.stroke(colorBeam);
      p.strokeWeight(2.0);

      p.line(x0, y0, x1, y1);

      // draw intersection
      if (laser.intersection !== Infinity) {
        const xi = laser.x + laser.m * laser.intersection;
        const yi = laser.intersection;
        p.circle(xi, yi, 10);
      }

      p.pop();

      // draw hover
      /* if (laser.hoverIntersection !== Infinity) {
        p.push();
        p.stroke(COLOR_LIGHT);
        p.strokeWeight(1.0);
        drawingContext.setLineDash([5, 10]);

        p.line(x0, y0, x1, y1);
        p.pop();
      } */
    }

    // draw cursor
    // p.noFill();
    // p.stroke(COLOR_LIGHT);
    // p.strokeWeight(1.0);

    // const [mx, my] = viewTransform.applyInverse(p.mouseX, p.mouseY);
    // p.circle(mx, my, CURSOR_SIZE);

    p.pop();

    // view key info
    p.fill(COLOR_LIGHT);
    p.noStroke();
    p.textSize(16);
    p.textAlign(p.LEFT, p.CENTER);

    const majorNote = new Note(currentScale.key);
    const minorNote = new Note(currentScale.key + 9);
    const keySignatureStr = `${majorNote.name}${majorNote.accidental || ""} / ${minorNote.name}${minorNote.accidental || ""}m`;
    p.text(`Key: ${keySignatureStr}`, 10, 20);
    p.text(`Octave: ${currentScale.octave}`, 130, 20);
    p.text(`Mode: ${currentScale.mode}`, 240, 20);
    p.text(`Midi In: "${LHIN_PORT}"`, 10, 45);
    p.text(`Midi Out: "${LHOUT_PORT}"`, 130, 45);

    // p.textAlign(p.RIGHT, p.CENTER);
    // for (let i = 0; i < messageConsole.length; i++) {
    //   const message = messageConsole[i];
    //   if (i === messageConsole.length - 1) {
    //     p.fill(COLOR_LIGHT);
    //   } else {
    //     p.fill(COLOR_LIGHT + "80");
    //   }
    //   p.text(message, p.width - 10, 20 + i * 15);
    // }
  };

  p.windowResized = () => {
    p.resizeCanvas(p.windowWidth, p.windowHeight);
  };

  p.mouseMoved = () => {
    // updateIntersections();
  }

  p.mouseDragged = () => {
    updateIntersections();
  }

  p.mousePressed = () => {
    updateIntersections();
  }

  p.mouseReleased = () => {
    updateIntersections();
  }
};
