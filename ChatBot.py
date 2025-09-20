import os
import re
import textwrap
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from youtube_transcript_api import YouTubeTranscriptApi,TranscriptsDisabled


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("GROQ_API_KEY")
os.environ['GROQ_API_KEY'] = api_key

chat = ChatGroq(model='llama-3.1-8b-instant')

def formatar_texto(texto, largura=100):
    return "\n".join(textwrap.wrap(texto, width=largura))

def resposta_bot(mensagens, documento):
  mensagem_system = '''Você é um assistente amigável chamado Habot.
  Você utiliza as seguintes informações para formular as suas respostas: {informacoes}'''
  mensagens_modelo = [('system', mensagem_system)]
  mensagens_modelo += mensagens
  template = ChatPromptTemplate.from_messages(mensagens_modelo)
  chain = template | chat
  return chain.invoke({'informacoes': documento}).content


def carrega_video():
    url_youtube = input("Digite a url do vídeo: ")
    video_id = None

    # Extrair ID da URL
    match_v = re.search(r'(?<=v=)[a-zA-Z0-9_-]{11}', url_youtube)
    if match_v:
        video_id = match_v.group(0)
    else:
        match_short = re.search(r'(?<=youtu\.be/)[a-zA-Z0-9_-]{11}', url_youtube)
        if match_short:
            video_id = match_short.group(0)

    if not video_id:
        print("Erro: Não foi possível extrair o ID do vídeo da URL.")
        return ""

    try:
        # Primeiro tenta pegar em português
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'pt-BR'])
        except:
            # Se não achar em pt, pega a primeira legenda disponível
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcripts.find_transcript([t.language_code for t in transcripts])
            transcript_list = transcript.fetch()

        full_transcript = " ".join([d['text'] for d in transcript_list])

        full_transcript_formatado = formatar_texto(full_transcript, 100)

        # Debug: mostrar um pedaço
        print("\n--- Prévia de transcrição ---")
        print(full_transcript_formatado[:500])  # mostra só os 500 primeiros caracteres
        print("\n--- ... ---")

        return full_transcript_formatado

    except TranscriptsDisabled:
        print("O vídeo não tem transcrição disponível (legendas desabilitadas).")
    except Exception as e:
        print(f"Erro ao buscar transcrição: {e}")


def carrega_site():
    url_site = input("Digite a url do site: ")
    try:
        print("Carregando conteúdo do site, por favor aguarde...")
        loader = WebBaseLoader(url_site)
        lista_documentos = loader.load()
        documento = ''
        for doc in lista_documentos:
            documento = documento + doc.page_content
        print("Conteúdo carregado com sucesso!")
        return documento
    except Exception as e:
        print(f"Não foi possível carregar o site. Erro: {e}")
        return None


print("Bem vindo ao HaBot")
texto_selecao = '''Comece carregando uma fonte de dados ou faça uma pergunta.
Comandos disponíveis:
Digite 1 - Para conversar com um site.
Digite 2 - Para conversar com um vídeo do Youtube.
Digite x - Para encerrar a conversa.
'''
print("-" * 50)

documento = None


while True:
  selecao = input(texto_selecao).strip().lower()

  if selecao == '1':
    print("Você escolheu conversar com um site")
    documento = carrega_site()
    if documento:
        break
    else:
        print("Tente carregar um site novamente ou escolha outra opção.")


  elif selecao == '2':
    print("Você escolheu conversar com um video do Youtube")
    documento = carrega_video()
    if documento:
        break
    else:
        print("Tente carregar um vídeo novamente ou escolha outra opção.")


  elif selecao.lower() == 'x':
     break

else:
    print("Opção inválida. Por favor, digite 1, 2 ou x.")

if documento:
    print("\n--- Início do Chat ---")
    print("Documento carregado. Faça suas perguntas ou digite 'x' para sair.")
    mensagens = []

    while True:
        pergunta = input("Usuário: ")
        if pergunta.lower() == 'x':
            break

        mensagens.append(('user', pergunta))
        resposta = resposta_bot(mensagens,documento)
        mensagens.append(('assistant', resposta))
        print(f"\nHaBot:\n{resposta}\n")

print("Obrigado por usar o HaBot")
print(mensagens)
