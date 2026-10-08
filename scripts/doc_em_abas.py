"""Cria o Doc da leva no Google Docs, com uma aba por roteiro.

A conversao de HTML do Drive nao cria aba, e o export do Claude Docs leva so'
a aba aberta. Aba de verdade so' sai pela API do Docs, e por isso este arquivo
fala com ela direto.

O visual e' o do gerador de levas do acervoroteiros: titulo, rotulos pequenos
na cor da casa, gancho e fechamento numa caixa com fundo, corpo em Arial 12.
Tempo, alavanca, tipo e fonte nao entram: pedido dele em 26/09.

Uso:
    python3 -m scripts.doc_em_abas <leva.json>
"""

import pathlib
import sys

PRIMARIA = "#2f3e4e"
CAIXA = "#f5f3ef"
TEXTO = "#222222"
FONTE = "Arial"
LIMITE_DA_ABA = 50
TRAVESSOES = (chr(0x2014), chr(0x2013))


def _cor(hexa):
    h = hexa.lstrip("#")
    return {"color": {"rgbColor": {"red": int(h[0:2], 16) / 255,
                                   "green": int(h[2:4], 16) / 255,
                                   "blue": int(h[4:6], 16) / 255}}}


def _pt(n):
    return {"magnitude": n, "unit": "PT"}


def _u16(texto):
    return len(texto.encode("utf-16-le")) // 2


def _paragrafos(texto):
    return [p.strip() for p in texto.split("\n") if p.strip()]


def blocos(roteiro):
    """(estilo, texto) na ordem em que aparecem na aba."""
    b = [("titulo", roteiro.get("titulo") or roteiro["tema"])]
    if roteiro.get("gravacao"):
        b.append(("rotulo", "GRAVAÇÃO E EDIÇÃO"))
        b += [("texto", p) for p in _paragrafos(roteiro["gravacao"])]
    b += [("rotulo", "GANCHO · PRIMEIROS SEGUNDOS"), ("caixa", roteiro["gancho"].strip())]
    b.append(("rotulo", "CORPO"))
    b += [("texto", p) for p in _paragrafos(roteiro["corpo"])]
    b += [("rotulo", "FECHAMENTO E CHAMADA"), ("caixa", roteiro["fechamento"].strip())]
    if roteiro.get("referencias"):
        b.append(("rotulo", "REFERÊNCIAS"))
        b += [("texto", "• " + ref) for ref in roteiro["referencias"]]
    return b


def _estilo(estilo, faixa):
    texto = {"weightedFontFamily": {"fontFamily": FONTE}, "fontSize": _pt(12),
             "foregroundColor": _cor(TEXTO), "bold": False}
    paragrafo = {"lineSpacing": 150, "spaceBelow": _pt(6), "spaceAbove": _pt(0)}
    if estilo == "titulo":
        texto.update(fontSize=_pt(16), foregroundColor=_cor(PRIMARIA), bold=True)
        paragrafo.update(namedStyleType="HEADING_1", spaceBelow=_pt(10))
    elif estilo == "rotulo":
        texto.update(fontSize=_pt(9), foregroundColor=_cor(PRIMARIA), bold=True)
        paragrafo.update(spaceAbove=_pt(12), spaceBelow=_pt(4))
    elif estilo == "caixa":
        texto.update(bold=True)
        borda = {"color": _cor(PRIMARIA), "width": _pt(0.5), "padding": _pt(8),
                 "dashStyle": "SOLID"}
        paragrafo.update(shading={"backgroundColor": _cor(CAIXA)}, borderTop=borda,
                         borderBottom=borda, borderLeft=borda, borderRight=borda)
    return [
        {"updateTextStyle": {"range": faixa, "textStyle": texto,
                             "fields": ",".join(texto)}},
        {"updateParagraphStyle": {"range": faixa, "paragraphStyle": paragrafo,
                                  "fields": ",".join(paragrafo)}},
    ]


def requisicoes_da_aba(roteiro, tab_id):
    b = blocos(roteiro)
    for _, t in b:
        if any(x in t for x in TRAVESSOES):
            raise ValueError(f"{roteiro.get('chave')}: travessao no texto, a varredura deixou passar")
    texto = "\n".join(t for _, t in b) + "\n"
    reqs = [{"insertText": {"location": {"index": 1, "tabId": tab_id}, "text": texto}}]
    inicio = 1
    for estilo, t in b:
        fim = inicio + _u16(t) + 1
        reqs += _estilo(estilo, {"startIndex": inicio, "endIndex": fim, "tabId": tab_id})
        inicio = fim
    return reqs


def nome_da_aba(n, roteiro):
    nome = f"Roteiro {n} · {roteiro['tema']}"
    return nome if len(nome) <= LIMITE_DA_ABA else nome[:LIMITE_DA_ABA - 1].rstrip() + "…"


def titulo_do_doc(leva):
    ano, mes, dia = leva["data"].split("-")
    return f"{leva['nome']} · Leva {dia}/{mes}"


RAIZ = pathlib.Path(__file__).resolve().parents[1]
CONFIG = pathlib.Path("~/.config/setor-de-roteiros").expanduser()
CLIENTE_GOOGLE = RAIZ / "config" / "google-client.json"
TOKEN = CONFIG / "google-token.json"
ESCOPOS = ["https://www.googleapis.com/auth/documents",
           "https://www.googleapis.com/auth/drive.file"]
PASTA_RAIZ = "Setor de Roteiros"
PASTA_MIME = "application/vnd.google-apps.folder"


def conectar():
    """Login do Google de quem esta usando. Na primeira vez abre o navegador."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    cred = Credentials.from_authorized_user_file(str(TOKEN), ESCOPOS) if TOKEN.exists() else None
    if cred and cred.expired and cred.refresh_token:
        try:
            cred.refresh(Request())
        except Exception:
            cred = None
    if not cred or not cred.valid:
        if not CLIENTE_GOOGLE.exists():
            raise SystemExit("falta config/google-client.json: siga docs/google-cloud.md")
        fluxo = InstalledAppFlow.from_client_secrets_file(str(CLIENTE_GOOGLE), ESCOPOS)
        cred = fluxo.run_local_server(port=0)
        CONFIG.mkdir(parents=True, exist_ok=True)
        TOKEN.write_text(cred.to_json(), encoding="utf-8")
    return build("docs", "v1", credentials=cred), build("drive", "v3", credentials=cred)


def _pasta(drive, nome, mae=None):
    nome_q = nome.replace("'", "\\'")
    q = f"name = '{nome_q}' and mimeType = '{PASTA_MIME}' and trashed = false"
    if mae:
        q += f" and '{mae}' in parents"
    achadas = drive.files().list(q=q, fields="files(id)", spaces="drive").execute()["files"]
    if achadas:
        return achadas[0]["id"]
    corpo = {"name": nome, "mimeType": PASTA_MIME}
    if mae:
        corpo["parents"] = [mae]
    return drive.files().create(body=corpo, fields="id").execute()["id"]


def criar(leva, servicos=None):
    docs, drive = servicos or conectar()
    roteiros = leva["roteiros"]
    pedidos = [requisicoes_da_aba(r, "a conferir") for r in roteiros]  # trava antes de criar
    del pedidos

    doc_id = docs.documents().create(body={"title": titulo_do_doc(leva)}).execute()["documentId"]
    completo = docs.documents().get(documentId=doc_id, includeTabsContent=True).execute()
    ids = [completo["tabs"][0]["tabProperties"]["tabId"]]

    if len(roteiros) > 1:
        novas = [{"addDocumentTab": {"tabProperties": {"title": nome_da_aba(i, r), "index": i - 1}}}
                 for i, r in enumerate(roteiros[1:], 2)]
        resposta = docs.documents().batchUpdate(documentId=doc_id, body={"requests": novas}).execute()
        ids += [rep["addDocumentTab"]["tabProperties"]["tabId"] for rep in resposta["replies"]]

    reqs = [{"updateDocumentTabProperties": {
        "tabProperties": {"tabId": ids[0], "title": nome_da_aba(1, roteiros[0])},
        "fields": "title"}}]
    for tab_id, r in zip(ids, roteiros):
        reqs += requisicoes_da_aba(r, tab_id)
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()

    destino = _pasta(drive, leva["nome"], _pasta(drive, PASTA_RAIZ))
    drive.files().update(fileId=doc_id, addParents=destino, removeParents="root",
                         fields="id").execute()
    return f"https://docs.google.com/document/d/{doc_id}/edit"


def main(argv):
    from scripts import leva as modulo_leva
    if len(argv) != 2:
        print(__doc__)
        return 1
    caminho = pathlib.Path(argv[1])
    dado = modulo_leva.ler(caminho)
    dado["doc_url"] = criar(dado)
    modulo_leva.atualizar(caminho, dado)
    print(dado["doc_url"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
