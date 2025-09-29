import os
import requests
import json
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Carrega as "chaves secretas" do ambiente
TOKEN_DE_ACESSO = os.environ.get('TOKEN_DE_ACESSO')
ID_DO_NUMERO_DE_TELEFONE = os.environ.get('ID_DO_NUMERO_DE_TELEFONE')
TOKEN_DE_VERIFICACAO = os.environ.get('TOKEN_DE_VERIFICACAO')

# Função para enviar mensagens de texto simples
def enviar_mensagem_texto(numero_destino, mensagem):
    url = f"https://graph.facebook.com/v20.0/{ID_DO_NUMERO_DE_TELEFONE}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN_DE_ACESSO}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": mensagem},
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP ao enviar mensagem: {err}")
        print(f"Corpo da resposta: {response.text}")

# --- NOVA FUNÇÃO PARA ENVIAR MENSAGENS COM BOTÕES ---
def enviar_mensagem_com_botoes(numero_destino, texto_corpo, botoes):
    url = f"https://graph.facebook.com/v20.0/{ID_DO_NUMERO_DE_TELEFONE}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN_DE_ACESSO}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": texto_corpo
            },
            "action": {
                "buttons": botoes
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP ao enviar mensagem com botões: {err}")
        print(f"Corpo da resposta: {response.text}")

# Rota do Webhook
@app.route("/", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == TOKEN_DE_VERIFICACAO:
            return request.args.get('hub.challenge'), 200
        else:
            return "Erro de verificação. Token inválido.", 403

    if request.method == 'POST':
        dados_recebidos = request.json
        print(json.dumps(dados_recebidos, indent=2))

        try:
            change = dados_recebidos['entry'][0]['changes'][0]
            if 'messages' in change['value']:
                mensagem_info = change['value']['messages'][0]
                numero_remetente = mensagem_info['from']
                tipo_mensagem = mensagem_info['type']

                # Lógica para mensagens de texto
                if tipo_mensagem == 'text':
                    mensagem_texto = mensagem_info['text']['body'].lower()
                    if "oi" in mensagem_texto or "olá" in mensagem_texto or "menu" in mensagem_texto:
                        texto_menu = (
                            "Olá! 💪 Bem-vindo à Nova União Guarulhos!\n\n"
                            "Eu sou o assistente virtual. Como posso te ajudar hoje?"
                        )
                        botoes_menu = [
                            {"type": "reply", "reply": {"id": "ver_horarios", "title": "Ver Horários"}},
                            {"type": "reply", "reply": {"id": "ver_planos", "title": "Planos e Preços"}},
                            {"type": "reply", "reply": {"id": "agendar_aula", "title": "Agendar Aula"}}
                        ]
                        enviar_mensagem_com_botoes(numero_remetente, texto_menu, botoes_menu)
                    else:
                        resposta_padrao = "Desculpe, não entendi. Digite 'oi' para ver as opções do menu principal."
                        enviar_mensagem_texto(numero_remetente, resposta_padrao)
                
                # --- NOVA LÓGICA PARA TRATAR CLIQUE EM BOTÃO ---
                elif tipo_mensagem == 'interactive' and 'button_reply' in mensagem_info['interactive']:
                    id_botao = mensagem_info['interactive']['button_reply']['id']
                    
                    if id_botao == 'ver_horarios':
                        horarios_texto = (
                            "Nossos horários são:\n\n"
                            "🥋 *Jiu-Jitsu Adulto:*\n"
                            "Segunda a Sexta: 07:00 - 16:00\n\n"
                            "🥋 *Jiu-Jitsu Kids:*\n"
                            "Terça e Quinta: 19:30\n\n" 
                            "Para voltar ao menu, digite 'oi'."
                        )
                        enviar_mensagem_texto(numero_remetente, horarios_texto)

                    elif id_botao == 'ver_planos':
                        planos_texto = (
                            "Temos os seguintes planos:\n\n"
                            "*Plano Adulto (3x por semana ou +):* R$ 150,00/mês\n"
                            "*Plano Competidor (treino indiviual):* R$ 80,00/aula\n"
                            "*Plano Kids:* R$ 120,00/mês\n\n"
                            "Para voltar ao menu, digite 'oi'."
                        )
                        enviar_mensagem_texto(numero_remetente, planos_texto)
                    
                    elif id_botao == 'agendar_aula':
                        agendamento_texto = (
                            "Ótima escolha! Para agendar sua aula experimental gratuita, por favor, contate diretamente por este link do WhatsApp para conversarmos com um de nossos professores: "
                            "https://wa.me/5511960965638" # <-- ATENÇÃO: Troque pelo seu número
                        )
                        enviar_mensagem_texto(numero_remetente, agendamento_texto)
        except (KeyError, IndexError):
            pass

        return "OK", 200

# Rota para exibir a página de pagamento PIX
@app.route("/pix")
def mostrar_pagina_pix():
    return render_template('pix.html')
