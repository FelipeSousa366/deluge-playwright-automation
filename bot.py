from playwright.sync_api import sync_playwright
from playwright._impl._errors import TargetClosedError
import keyboard
import time

LEGENDARY_TEXT = "Legendary Pokemon"
CDP_URL = "http://localhost:9222"  
lend_num=0

def get_deluge_page(browser):
    """Procura uma aba com delugerpg.com aberta."""
    for context in browser.contexts:
        for page in context.pages:
            if "delugerpg.com" in page.url:
                return page
    return None


def check_legendary(page) -> bool:
    """Retorna True se o Pokémon atual é lendário, False caso contrário."""
    locator = page.locator("#mapcontext.basic")

    count = locator.count()

    if count == 0:
        return False

    text = locator.inner_text(timeout=1000).strip()
    return len(text) > 0

def catch_legendary(page):
    print("Lendário encontrado! Iniciando sequência de captura...")

    # 1) Clicar em "Try to Catch It"
    page.wait_for_selector("#catchmon", timeout=10000)
    page.click("#catchmon")

    # 2) Clicar em "Start Battle"
    page.wait_for_selector('input.btn-battle_action[name="Start Battle"]', timeout=10000)
    page.click('input.btn-battle_action[name="Start Battle"]')

    # 3) Selecionar Master Ball
    page.wait_for_selector("#item-masterball", timeout=10000)
    page.check("#item-masterball")  # marca o radio

    # 4) Clicar em "Throw Master Ball"
    page.wait_for_selector('input.btn-battle_action[name="useitem_"]', timeout=10000)
    page.click('input.btn-battle_action[name="useitem_"]')

    # 5) Clicar em "Return to Map"
    page.wait_for_selector('a.btn.btn-primary[href="/map"]', timeout=15000)
    page.click('a.btn.btn-primary[href="/map"]')

    # Garante que voltou pro mapa
    page.wait_for_load_state("networkidle")
    print("✅ Captura concluída, de volta ao mapa. Retomando busca...")
    global lend_num
    lend_num += 1
    print(f"Total de lendários capturados: {lend_num}")

def search_for_legendary(page) -> bool:
    """
    Fica andando (A/D) até encontrar lendário.
    Retorna True se encontrar, False se for interrompido por erro externo.
    """
    while True:
        # Press A
        page.keyboard.press("A")
        page.wait_for_timeout(50)
        found_a = check_legendary(page)
        #print(f"A -> Legendary? {found_a}")
        if found_a:
            return True

        # Press D
        page.keyboard.press("D")
        page.wait_for_timeout(50)
        found_d = check_legendary(page)
        #print(f"D -> Legendary? {found_d}")
        if found_d:
            return True

def run_automation_cycle(page):
    """
    Um ciclo completo: procurar lendário, capturar, voltar ao mapa.
    """
    # Tenta dar foco, mas não trava se falhar
    try:
        page.click("body", timeout=3000)
    except Exception:
        try:
            page.evaluate("window.focus()")
        except:
            pass

    # 1) Procurar lendário
    found = search_for_legendary(page)
    if not found:
        return False  # se quiser tratar depois

    # 2) Capturar lendário
    catch_legendary(page)
    return True


def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

        page = get_deluge_page(browser)
        if not page:
            print(" Aba do jogo não encontrada. Abra delugerpg.com no Edge/Chrome debug e tecle ENTER.")
            input()
            page = get_deluge_page(browser)
            if not page:
                print("Ainda não encontrei a aba. Encerrando.")
                return

        print(f"📄 Conectado à aba: {page.url}")

        # Espera carregamento básico
        try:
            page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass

        print("⏳ Pressione F2 para iniciar a automação.")
        keyboard.wait("f2")

        # Loop infinito: procurar + capturar + voltar ao mapa + repetir
        while True:
            try:
                ok = run_automation_cycle(page)
                if not ok:
                    print(" Ciclo terminado sem sucesso. Interrompendo.")
                    break

                # Pequena pausa entre um lendário e outro (opcional)
                time.sleep(0.5)

            except TargetClosedError:
                print("Conexão perdida. Tentando reconectar em 2s...")
                time.sleep(2)

                try:
                    browser = p.chromium.connect_over_cdp(CDP_URL)
                except Exception as e:
                    print(f"Não consegui reconectar ao navegador: {e}")
                    break

                page = get_deluge_page(browser)
                if not page:
                    print(" Aba do jogo não encontrada. Abra o jogo e tecle ENTER.")
                    input()
                    page = get_deluge_page(browser)
                    if not page:
                        print("Ainda não achei a aba. Encerrando.")
                        break

                print("Reconectado. Retomando busca automática...")

            except Exception as e:
                print(f"Erro inesperado: {e}")
                print("Pausando 3s e tentando continuar...")
                time.sleep(3)

        print("Script finalizado.")


if __name__ == "__main__":
    main()