#!/usr/bin/env python3
import json
import time
import requests
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

# Адрес Ollama (нативный запуск на ноутбуке)
OLLAMA_URL = "http://localhost:11434/api/chat"
# Название модели, которую мы собрали вручную (можешь поменять на qwen2.5:0.5b, если скачал через Docker)
MODEL = "qwen-local:latest" 

SYSTEM_PROMPT = (
    "Ты — контроллер робота-черепашки. Твоя задача — переводить команды в JSON.\n"
    "Формат ответа: {\"action\": string, \"value\": float}\n\n"
    "ПРАВИЛА:\n"
    "1. Вперед (forward, go): {\"action\": \"forward\", \"value\": 1.0}\n"
    "2. Назад (back): {\"action\": \"backward\", \"value\": -1.0}\n"
    "3. Налево (left, turn left): {\"action\": \"turn_left\", \"value\": 1.57}\n"
    "4. Направо (right, turn right): {\"action\": \"turn_right\", \"value\": -1.57}\n"
    "5. Квадрат (square): {\"action\": \"square\", \"value\": 0.0}\n"
    "6. Треугольник (triangle): {\"action\": \"triangle\", \"value\": 0.0}\n"
    "7. Стоп (stop): {\"action\": \"stop\", \"value\": 0.0}\n\n"
    "ЗАПРЕЩЕНО писать текст, объяснения или markdown (например, ```json).\n"
    "Отвечай ТОЛЬКО валидным JSON."
)

class TurtleLLMNode(Node):
    def __init__(self):
        super().__init__('turtle_llm_node')
        self.sub = self.create_subscription(String, '/nlp_command', self.on_text, 10)
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.get_logger().info('Нода запущена. Жду команды в /nlp_command...')

    def move(self, linear, angular, duration):
        twist = Twist()
        # Safety Limiter: жестко ограничиваем скорость
        twist.linear.x = max(min(linear, 1.0), -1.0)
        twist.angular.z = max(min(angular, 1.57), -1.57)
        self.pub.publish(twist)
        time.sleep(duration)
        # Обязательная остановка после команды
        self.pub.publish(Twist())

    def draw_square(self):
        self.get_logger().info("Рисую квадрат...")
        for _ in range(4):
            self.move(1.0, 0.0, 2.0)  # Вперед 2 сек
            self.move(0.0, 1.57, 1.0) # Поворот налево 1 сек (на 90 градусов)

    def draw_triangle(self):
        self.get_logger().info("Рисую треугольник...")
        for _ in range(3):
            self.move(1.0, 0.0, 2.5)  # Вперед 2.5 сек
            self.move(0.0, 1.57, 1.2) # Поворот налево 1.2 сек (на 120 градусов)

    def on_text(self, msg):
        text = msg.data
        self.get_logger().info(f'Получен текст: "{text}"')
        
        try:
            response = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0}
            }, timeout=120)
            
            content = response.json()["message"]["content"]
            # Очистка от возможных артефактов
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            
            action = result.get("action", "stop")
            value = float(result.get("value", 0.0))
            
            self.get_logger().info(f'Распознано действие: {action} (value={value})')
            
            if action == "forward":
                self.move(abs(value), 0.0, 1.0)
            elif action == "backward":
                self.move(-abs(value), 0.0, 1.0)
            elif action == "turn_left":
                self.move(0.0, abs(value), 1.0)
            elif action == "turn_right":
                self.move(0.0, -abs(value), 1.0)
            elif action == "square":
                self.draw_square()
            elif action == "triangle":
                self.draw_triangle()
            else:
                self.get_logger().info("Команда 'стоп' или неизвестная. Останавливаюсь.")
                self.pub.publish(Twist())
                
        except Exception as e:
            self.get_logger().error(f'Ошибка LLM или парсинга: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = TurtleLLMNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
