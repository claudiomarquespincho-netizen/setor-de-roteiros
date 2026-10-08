import pytest

from scripts import doc_em_abas as d

ROTEIRO = {"chave": "r1", "tema": "Jaleco do instituto", "gravacao": "Lo-fi.",
           "gancho": "Gancho aqui.", "corpo": "Primeiro.\nSegundo.", "fechamento": "Fecho."}


def test_blocos_na_ordem():
    estilos = [e for e, _ in d.blocos(ROTEIRO)]
    assert estilos == ["titulo", "rotulo", "texto", "rotulo", "caixa",
                       "rotulo", "texto", "texto", "rotulo", "caixa"]


def test_sem_gravacao_nao_tem_bloco_de_gravacao():
    r = dict(ROTEIRO, gravacao="")
    assert "GRAVAÇÃO E EDIÇÃO" not in [t for _, t in d.blocos(r)]


def test_titulo_usa_titulo_quando_existe():
    assert d.blocos(dict(ROTEIRO, titulo="Outro"))[0] == ("titulo", "Outro")


def test_nada_de_tempo_alavanca_ou_fonte():
    r = dict(ROTEIRO, alavanca="medo", fonte="Folha", tempo="60s", tipo="utilidade")
    texto = " ".join(t for _, t in d.blocos(r))
    assert "medo" not in texto and "Folha" not in texto and "60s" not in texto
    assert "utilidade" not in texto


def test_requisicoes_inserem_tudo_na_aba_certa():
    reqs = d.requisicoes_da_aba(ROTEIRO, "t.abc")
    insere = reqs[0]["insertText"]
    assert insere["location"] == {"index": 1, "tabId": "t.abc"}
    assert insere["text"].startswith("Jaleco do instituto\n")
    for req in reqs[1:]:
        corpo = next(iter(req.values()))
        assert corpo["range"]["tabId"] == "t.abc"


def test_faixas_contam_utf16():
    r = dict(ROTEIRO, gravacao="", gancho="Olá 😀.")
    reqs = d.requisicoes_da_aba(r, "t")
    texto = reqs[0]["insertText"]["text"]
    fim = max(next(iter(q.values()))["range"]["endIndex"] for q in reqs[1:])
    assert fim == 1 + len(texto.encode("utf-16-le")) // 2


def test_caixa_tem_fundo():
    reqs = d.requisicoes_da_aba(ROTEIRO, "t")
    sombreados = [q for q in reqs if "updateParagraphStyle" in q
                  and "shading" in q["updateParagraphStyle"]["paragraphStyle"]]
    assert len(sombreados) == 2


def test_nome_da_aba():
    assert d.nome_da_aba(1, ROTEIRO) == "Roteiro 1 · Jaleco do instituto"
    longo = dict(ROTEIRO, tema="x" * 80)
    assert len(d.nome_da_aba(2, longo)) <= 50


def test_titulo_do_doc():
    assert d.titulo_do_doc({"nome": "Cici", "data": "2026-10-08"}) == "Cici · Leva 08/10"


def test_travessao_recusa():
    r = dict(ROTEIRO, corpo="isso " + chr(0x2014) + " aquilo")
    with pytest.raises(ValueError):
        d.requisicoes_da_aba(r, "t")


class _Chamada:
    def __init__(self, resposta):
        self.resposta = resposta

    def execute(self):
        return self.resposta


class _Documents:
    def __init__(self):
        self.lotes = []
        self.abas = 1

    def create(self, body):
        self.titulo = body["title"]
        return _Chamada({"documentId": "doc1"})

    def get(self, documentId, includeTabsContent):
        return _Chamada({"tabs": [{"tabProperties": {"tabId": "t.0"}}]})

    def batchUpdate(self, documentId, body):
        self.lotes.append(body["requests"])
        replies = []
        for req in body["requests"]:
            if "addDocumentTab" in req:
                replies.append({"addDocumentTab": {"tabProperties": {"tabId": f"t.{self.abas}"}}})
                self.abas += 1
            else:
                replies.append({})
        return _Chamada({"replies": replies})


class _Docs:
    def __init__(self):
        self.d = _Documents()

    def documents(self):
        return self.d


class _Files:
    def __init__(self):
        self.movido = None

    def list(self, q, fields, spaces="drive"):
        return _Chamada({"files": []})

    def create(self, body, fields):
        return _Chamada({"id": "pasta-" + body["name"]})

    def update(self, fileId, addParents, removeParents, fields):
        self.movido = addParents
        return _Chamada({"id": fileId})


class _Drive:
    def __init__(self):
        self.f = _Files()

    def files(self):
        return self.f


def test_criar_uma_aba_por_roteiro():
    docs, drive = _Docs(), _Drive()
    roteiros = [dict(ROTEIRO, chave=f"r{i}", tema=f"Tema {i}") for i in (1, 2, 3)]
    url = d.criar({"nome": "Cici", "data": "2026-10-08", "roteiros": roteiros}, (docs, drive))
    assert url == "https://docs.google.com/document/d/doc1/edit"
    assert docs.d.titulo == "Cici · Leva 08/10"
    ultimo = docs.d.lotes[-1]
    abas = {q["insertText"]["location"]["tabId"] for q in ultimo if "insertText" in q}
    assert abas == {"t.0", "t.1", "t.2"}
    renomeia = [q for q in ultimo if "updateDocumentTabProperties" in q]
    assert renomeia[0]["updateDocumentTabProperties"]["tabProperties"]["title"] == "Roteiro 1 · Tema 1"
    assert drive.f.movido == "pasta-Cici"
