import pydircbot.config


def main():
    config = pydircbot.config.ConfigManager()
    print(config.config)


if __name__ == '__main__':
    main()
