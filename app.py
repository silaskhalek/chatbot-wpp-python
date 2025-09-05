# 1. Importa a classe Flask do pacote flask que instalamos
from flask import Flask

# 2. Cria a instância do nosso aplicativo web.
# A variável __name__ ajuda o Flask a saber onde ele está.
app = Flask(__name__)

# 3. Define uma "rota" para a página inicial ("/").
# O @ é um "decorator" que adiciona uma funcionalidade à função abaixo.
# Basicamente, ele diz: "Quando alguém acessar a página inicial do site, execute esta função".
@app.route("/")
def hello_world():
    # 4. Esta função retorna o texto que será exibido no navegador.
    return "<p>Nosso chatbot está no ar e esperando o WhatsApp chamar!</p>"