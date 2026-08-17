import os
import zipfile
from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

# =====================================================================
# CARREGAMENTO DAS VARIÁVEIS DE AMBIENTE (.env)
# =====================================================================
load_dotenv()
URL_SANSYS = os.getenv("URL_SANSYS")
URL_SP_SITE = os.getenv("URL_SP_SITE")
URL_SP_PASTA = os.getenv("URL_SP_PASTA")

# =====================================================================
# FUNÇÃO 1: BAIXAR O RELATÓRIO
# =====================================================================
def baixar_relatorio(playwright: Playwright, usuario_sansys: str, senha_sansys: str, invisivel: bool) -> str:
    browser = playwright.chromium.launch(headless=invisivel)
    context = browser.new_context()
    page = context.new_page()
    
    print("\n--- INICIANDO EXTRAÇÃO WEB ---")
    page.goto(URL_SANSYS) # Usando a variável do .env
    
    page.get_by_placeholder("Usuário").click(force=True)
    page.get_by_placeholder("Usuário").fill(usuario_sansys, force=True)
    page.get_by_placeholder("Usuário").press("Tab")
    
    page.get_by_placeholder("Senha").fill(senha_sansys, force=True)
    page.get_by_placeholder("Senha").press("Enter")
    page.wait_for_timeout(2000)
    page.get_by_placeholder("Senha").press("Enter")   
    
    page.wait_for_timeout(5000)
    
    page.locator("i.material-icons", has_text="menu").click()
    page.wait_for_timeout(3000)

    page.get_by_text("Gerencial", exact=True).click()
    page.get_by_text("Relatório Customizado", exact=True).click()
    page.get_by_text("Processar Relatório Fonte de Dado", exact=True).click()
    page.wait_for_timeout(3000)

    page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_header"]').click()
    page.locator('div[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.cdRelatorioFonteDado_cell"]').get_by_text("075", exact=True).first.click()
    page.locator('button[cfgname="processarRelatorioFonteDadoSansys.pesquisar.infRelatorioFonteDados.icAbrir"]').first.click()
    page.wait_for_timeout(3000)
    
    page.locator("img.x-form-date-trigger:visible").first.click()
    page.wait_for_timeout(500) 
    page.locator("button:visible", has_text="Hoje").first.click()
    
    page.get_by_role("textbox", name="Grupo Faturamento (Informe 0").fill("0", force=True)
    page.wait_for_timeout(3000)
    
    page.get_by_text("Executar", exact=True).click()

    botao_download = page.locator('button[cfgname="acompanharExecucaoRelatorioFonteDado.acompanhar.btDownload"]')
    botao_download.wait_for(state="visible", timeout=1200000)
    
    with page.expect_download(timeout=60000) as download_info:
        botao_download.click()
        
    download = download_info.value
    
    # Salva na pasta padrão de Downloads do usuário atual do Windows
    pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
    caminho_final = os.path.join(pasta_destino, download.suggested_filename)
    download.save_as(caminho_final)

    context.close()
    browser.close()
    
    return caminho_final

# =====================================================================
# FUNÇÃO 2: ENVIAR PARA O SHAREPOINT
# =====================================================================
def enviar_sharepoint(caminho_zip: str, email_sp: str, senha_sp: str):
    print("\n--- INICIANDO PROCESSAMENTO E UPLOAD ---")
    pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
    pasta_extracao = os.path.join(pasta_destino, "Relatorio_Temporario")
    os.makedirs(pasta_extracao, exist_ok=True)

    with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
        zip_ref.extractall(pasta_extracao)
        nome_excel_extraido = zip_ref.namelist()[0] 

    caminho_arquivo_excel = os.path.join(pasta_extracao, nome_excel_extraido)

    # Usando as variáveis do .env e as senhas da tela
    ctx = ClientContext(URL_SP_SITE).with_credentials(UserCredential(email_sp, senha_sp)) 
    pasta_sp = ctx.web.get_folder_by_server_relative_url(URL_SP_PASTA)
    
    nome_no_sharepoint = "Relatorio_Analitico_Matriculas_Atualizado.xlsx" 

    with open(caminho_arquivo_excel, "rb") as arquivo:
        pasta_sp.upload_file(nome_no_sharepoint, arquivo.read())
        ctx.execute_query()

# =====================================================================
# FUNÇÃO PRINCIPAL (CHAMADA PELA TELA)
# =====================================================================
def executar_robo_completo(usuario_sansys, senha_sansys, email_sp, senha_sp, invisivel=True):
    try:
        with sync_playwright() as playwright:
            arquivo_baixado = baixar_relatorio(playwright, usuario_sansys, senha_sansys, invisivel)
        enviar_sharepoint(arquivo_baixado, email_sp, senha_sp)
        
        # Se tudo deu certo, retorna True e a mensagem de sucesso
        return True, "Relatório extraído e enviado com sucesso!"
    except Exception as e:
        # Se der erro (senha errada, internet caiu), retorna False e o erro para a tela exibir
        return False, f"Ocorreu um erro durante a execução:\n{str(e)}"