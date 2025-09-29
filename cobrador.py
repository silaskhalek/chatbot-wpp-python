import os
import requests
import json
import csv
from datetime import datetime, timedelta

# Carrega as "chaves secretas" do ambiente
TOKEN_DE_ACESSO = os.environ.get('TOKEN_DE_ACESSO')
ID_DO_NUMERO_DE_TELEFONE = os.environ.get('ID_DO_NUMERO_DE_TELEFONE')
NUMERO_DO_SENSEI = os.environ.get('CELULAR_SENSEI') # <-- Variável necessária para o relatório

# --- ATENÇÃO: PREENCHA COM OS NOMES EXATOS DOS SEUS MODELOS APROVADOS ---
NOME_TEMPLATE_COBRANCA_HOJE = "lembrete_mensalidade1"
NOME_TEMPLATE_AVISO_VESPERA = "lembrete_mensalidade2"
# --------------------------------------------------------------------

# Função genérica para enviar mensagens de TEMPLATE (para alunos)
def enviar_mensagem_template(numero_destino, nome_template, parametros):
    url = f"https://graph.facebook.com/v20.0/{ID_DO_NUMERO_DE_TELEFONE}/messages"
    headers = {"Authorization": f"Bearer {TOKEN_DE_ACESSO}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp", "to": numero_destino, "type": "template",
        "template": {"name": nome_template, "language": {"code": "pt_BR"},
                     "components": [{"type": "body", "parameters": parametros}]}
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print(f"Mensagem do template '{nome_template}' enviada com sucesso para {numero_destino}")
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP ao enviar template '{nome_template}': {err}")
        print(f"Corpo da resposta: {response.text}")

# --- Função necessária para enviar o relatório para o sensei ---
def enviar_mensagem_texto(numero_destino, mensagem):
    url = f"https://graph.facebook.com/v20.0/{ID_DO_NUMERO_DE_TELEFONE}/messages"
    headers = {"Authorization": f"Bearer {TOKEN_DE_ACESSO}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": numero_destino, "type": "text", "text": {"body": mensagem}}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print(f"Relatório enviado com sucesso para o Sensei.")
    except requests.exceptions.HTTPError as err:
        print(f"--- ATENÇÃO: Erro ao enviar relatório para o Sensei: {err} ---")
        print("Isso geralmente acontece porque a 'janela de 24 horas' para conversa está fechada.")
        print(f"Corpo da resposta: {response.text}")


def verificar_vencimentos():
    hoje = datetime.now()
    amanha = hoje + timedelta(days=1)
    dia_hoje = hoje.day
    dia_amanha = amanha.day
    data_formatada = hoje.strftime("%d/%m/%Y")
    
    alunos_cobrados_hoje = [] # Lista apenas para quem vence hoje
    
    print(f"--- Iniciando verificação de vencimentos para o dia {dia_hoje} ---")

    if not all([TOKEN_DE_ACESSO, ID_DO_NUMERO_DE_TELEFONE, NUMERO_DO_SENSEI]):
        print("ERRO: Verifique se os secrets TOKEN_DE_ACESSO, ID_DO_NUMERO_DE_TELEFONE e NUMERO_DO_SENSEI estão configurados.")
        return

    try:
        with open('alunos.csv', mode='r', encoding='utf-8') as arquivo_csv:
            leitor_csv = csv.DictReader(arquivo_csv)
            for linha in leitor_csv:
                nome_aluno = linha['nome']
                numero_aluno = linha['whatsapp']
                dia_vencimento = int(linha['dia_vencimento'])
                valor_mensalidade_str = f"{float(linha['valor']):.2f}".replace('.', ',')

                if dia_vencimento == dia_hoje:
                    print(f"VENCIMENTO HOJE para: {nome_aluno}")
                    parametros_cobranca = [
                        {"type": "text", "text": nome_aluno},
                        {"type": "text", "text": valor_mensalidade_str}
                    ]
                    enviar_mensagem_template(numero_aluno, NOME_TEMPLATE_COBRANCA_HOJE, parametros_cobranca)
                    alunos_cobrados_hoje.append(nome_aluno) # <-- CORREÇÃO: Adiciona o nome à lista
                
                elif dia_vencimento == dia_amanha:
                    print(f"AVISO DE VÉSPERA para: {nome_aluno}")
                    parametros_aviso = [
                        {"type": "text", "text": nome_aluno},
                        {"type": "text", "text": valor_mensalidade_str}
                    ]
                    enviar_mensagem_template(numero_aluno, NOME_TEMPLATE_AVISO_VESPERA, parametros_aviso)
                
                else:
                    print(f"Sem notificação para: {nome_aluno} (vence dia {dia_vencimento})")

    except FileNotFoundError:
        print("ERRO: Arquivo 'alunos.csv' não encontrado. Crie o arquivo para continuar.")
        return

    # --- LÓGICA DE RELATÓRIO SIMPLIFICADA ---
    if alunos_cobrados_hoje:
        nomes_formatados = "\n".join([f"- {nome}" for nome in alunos_cobrados_hoje])
        texto_relatorio = (
            f"*Relatório de Cobranças - {data_formatada}*\n\n"
            f"Os seguintes alunos receberam um lembrete de mensalidade hoje:\n"
            f"{nomes_formatados}"
        )
        print("Enviando relatório para o Sensei...")
        enviar_mensagem_texto(NUMERO_DO_SENSEI, texto_relatorio)
    else:
        print("Nenhum aluno com vencimento hoje. Relatório não será enviado.")

    print("--- Verificação de vencimentos concluída ---")


if __name__ == "__main__":
    verificar_vencimentos()
