<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
</head>
<body>
  <h1>Описание проекта</h1>
  <p>
    Данный проект представляет собой веб-приложение с интеграцией в настольное приложение. Приложение разработано с использованием Flask для бэкенда, Tailwind CSS и кастомных стилей для фронтенда, а также Node.js для управления зависимостями. Кроме того, реализована интеграция с Qt для создания нативного окна.
  </p>

  <div class="divider"></div>

  <h2>Структура репозитория</h2>
  <pre>
├── chat_history/               # История сообщений чата
├── node_modules/               # Модули Node.js
├── static/                     # Статические файлы
│   ├── css/                    # Стили
│   │   ├── dist/               # Скомпилированные CSS-файлы
│   │   │   ├── output.css
│   │   │   ├── input.css
│   │   ├── main.css
│   │   └── style.css
│   ├── js/                     # Скрипты
│   │   └── chat.js
├── templates/                  # HTML-шаблоны
│   ├── chat.html
│   └── login.html
├── app.py                      # Основное Flask-приложение
├── voice_messages.py           # Поддержка голосовых сообщений
├── ip_history.json             # История IP-адресов
├── last_login.json             # Последний вход пользователя
├── package-lock.json           # Лок-файл зависимостей Node.js
├── package.json                # Зависимости Node.js
├── postcss.config.js           # Конфигурация PostCSS
├── tailwind.config.js          # Конфигурация Tailwind CSS
├── requirements.txt            # Список зависимостей Python
└── README.md                   # Описание проекта
  </pre>

  <div class="divider"></div>

  <h2>Установка зависимостей</h2>
  
  <h3>Python</h3>
  <p>Установите необходимые зависимости для Python:</p>
  <pre><code>pip install -r requirements.txt</code></pre>

  <h3>Node.js</h3>
  <p>Установите зависимости для Node.js:</p>
  <pre><code>npm install</code></pre>

  <div class="divider"></div>

  <h2>Запуск приложения</h2>
  <p>Запустите приложение командой:</p>
  <pre><code>python app.py</code></pre>
  <p>После запуска:</p>
  <ul>
    <li><strong>Flask-сервер</strong> будет доступен по адресу: <a href="http://127.0.0.1:5000" target="_blank">http://127.0.0.1:5000</a></li>
    <li><strong>WebSocket-сервер</strong> запустится на порту <strong>12345</strong></li>
    <li>Автоматически откроется нативное окно с использованием <strong>Qt</strong></li>
  </ul>

  <div class="divider"></div>

  <h2>Основные возможности</h2>

  <h3>Система авторизации</h3>
  <ul>
    <li>Ввод имени пользователя и IP-адреса сервера</li>
    <li>Отслеживание истории введённых IP</li>
    <li>Быстрый вход для повторных пользователей</li>
  </ul>

  <h3>Чат</h3>
  <ul>
    <li>Обмен сообщениями в реальном времени</li>
    <li>Возможность оставлять личные заметки</li>
    <li>Сохранение истории сообщений(временно отключено)</li>
    <li>Индикаторы состояния подключения</li>
    <li>Адаптивный дизайн для любых экранов</li>
  </ul>

  <h3>Интеграция с рабочим столом</h3>
  <ul>
    <li>Нативное настольное окно с использованием Qt</li>
    <li>Интегрированный веб-просмотр</li>
    <li>Интеграция с системным треем</li>
  </ul>
</body>
</html>
