from laserharp.mqtt_component import EndpointComponent, ConfigurableComponent, PUBLISH_ONLY_ACCESS, SUBSCRIBE_ONLY_ACCESS


class LaserDiode(EndpointComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.brightness = self.add_endpoint(
            "brightness",
            schema="""
            properties:
                value:
                    type: number
                    minimum: 0
                    maximum: 1
                    default: 1
            required:
                - value
            """,
            access=PUBLISH_ONLY_ACCESS,
        )
        self.interception = self.add_endpoint(
            "interception",
            schema="""
            properties:
                value:
                    type: number
                    minimum: 0
                    maximum: .inf
                    default: .inf
            required:
                - value
            """,
            access=SUBSCRIBE_ONLY_ACCESS,
        )


class LaserArray(ConfigurableComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_config(
            """
            type: object
            properties:
                num_lasers:
                    title: "Number of lasers"
                    minimum: 1
                    maximum: 255
                    default: 11
            required:
                - num_lasers
            """
        )

        self.lasers = [self.add_child(str(i), LaserDiode) for i in range(self.config.value["num_lasers"])]
