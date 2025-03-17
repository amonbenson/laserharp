import { ref, watch } from "vue";
import { $mqtt } from "vue-paho-mqtt";

const PUBLISH_INTERVAL = 100;

const topicCache = new Map();
const topicLastPublishTime = new Map();
const topicTimeouts = new Map();

export function subscribe(topic, callback, options = {}) {
  $mqtt.subscribe(topic, (payload) => {
    const parsedPayload = options.raw ? payload : JSON.parse(payload);
    callback(parsedPayload);
  }, false);
}

export function unsubscribe(topic) {
  $mqtt.unsubscribe(topic);
}

export function publish(topic, payload, options = {}) {
  const rawPayload = options.raw ? payload : JSON.stringify(payload);

  function doPublish () {
    $mqtt.publish(topic, topicCache.get(topic), options.mode ?? "B", false);
    topicLastPublishTime.set(topic, currentTime);
  }

  // if the payload is the same as the last one, don't publish again to avoid reactivity loops
  if (topicCache.has(topic) && topicCache.get(topic) === rawPayload) {
    return;
  }

  // set the cached payload
  topicCache.set(topic, rawPayload);

  // check if enough time has elapsed since the last publish, schedule a timeout to publish later
  const lastPublishTime = topicLastPublishTime.get(topic) ?? 0;
  const currentTime = Date.now();
  if (currentTime - lastPublishTime < PUBLISH_INTERVAL) {
    if (!topicTimeouts.has(topic)) {
      topicTimeouts.set(topic, setTimeout(() => {
        doPublish();
        topicTimeouts.delete(topic);
      }, PUBLISH_INTERVAL));
    }

    return;
  }

  doPublish();
}

export function useTopic(topic, options = {}) {
  const raw = options.raw ?? false;
  const mode = options.mode ?? "B";
  const defaultValue = options.default ?? null;

  const value = ref(defaultValue);

  // subscribe to all value updates
  subscribe(topic, (payload) => {
    value.value = payload;
  }, { raw });

  // publish value updates
  watch(value, (newValue) => {
    publish(topic, newValue, { raw, mode });
  }, { deep: true });

  return value;
}
