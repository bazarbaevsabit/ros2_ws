# ros2_ws

Рабочее пространство ROS 2 с пакетом `turtle_llm`: узел преобразует текстовые команды на русском или английском языке в действия для черепашки `turtlesim` с помощью локальной модели Ollama.

## Как это работает

1. Узел `turtle_llm_node` получает текст из топика `/nlp_command` (`std_msgs/msg/String`).
2. Отправляет текст локальному API Ollama (`http://localhost:11434/api/chat`), используя модель `qwen-local:latest`.
3. По ответу модели выполняет движение или рисует квадрат/треугольник, публикуя команды `geometry_msgs/msg/Twist` в `/turtle1/cmd_vel`.

Линейная и угловая скорости ограничены в коде узла. После каждого движения узел публикует команду остановки.

## Требования

- ROS 2 и инструменты сборки `colcon`.
- Пакет ROS 2 `turtlesim`.
- Python-пакет `requests`.
- [Ollama](https://ollama.com/) с запущенным локальным API и установленной моделью. По умолчанию используется `qwen-local:latest`; при необходимости измените `MODEL` в `src/turtle_llm/turtle_llm/nlp_interpreter.py` на имя доступной модели.

## Сборка

Выполните команды из корня рабочего пространства:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Если переменная `ROS_DISTRO` не задана, сначала выберите и установите поддерживаемый вами дистрибутив ROS 2.

## Запуск

Откройте отдельные терминалы и выполните в каждом из них команды для подключения окружения ROS 2 и рабочего пространства.

1. Запустите Ollama и убедитесь, что выбранная модель доступна:

   ```bash
   ollama serve
   ollama list
   ```

2. Запустите симулятор:

   ```bash
   ros2 run turtlesim turtlesim_node
   ```

3. Запустите узел обработки команд:

   ```bash
   ros2 run turtle_llm nlp_interpreter
   ```

4. Отправьте текстовую команду:

   ```bash
   ros2 topic pub --once /nlp_command std_msgs/msg/String "{data: 'нарисуй квадрат'}"
   ```

Можно отправлять команды вроде «вперед», «назад», «налево», «направо», «стоп», «квадрат» или «треугольник». Ответ Ollama должен быть валидным JSON с полями `action` и `value`.

## Структура

```text
ros2_ws/
└── src/
    └── turtle_llm/
        ├── package.xml
        ├── setup.py
        └── turtle_llm/
            └── nlp_interpreter.py
```

## Лицензия

Пакет `turtle_llm` распространяется под лицензией MIT. См. [`src/turtle_llm/LICENSE`](src/turtle_llm/LICENSE).
