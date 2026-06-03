from app import create_app

app = create_app()

# Без QR кода, чисто базовый пуск приложения

#if __name__ == '__main__':
#    app.run(debug=True)


# Для теста QR кода

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)   