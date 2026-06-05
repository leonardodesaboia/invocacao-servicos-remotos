"""
Correção de compatibilidade do spyne 2.14 com Python 3.12+.

O `six` embutido no spyne (`spyne.util.six`) traz seu próprio importador de
módulos (`_SixMetaPathImporter`) que implementa apenas a API ANTIGA
(`find_module`/`load_module`). O Python 3.12 deixou de consultar essa API e
passou a exigir `find_spec`, então o submódulo `spyne.util.six.moves` (e seus
submódulos: `collections_abc`, `http_cookies`, `urllib.parse`, ...) não é
encontrado e o spyne sequer importa:

    ModuleNotFoundError: No module named 'spyne.util.six.moves'

Solução robusta: carregamos o six embutido do spyne (preservando suas funções
extras, como `get_function_name`, que o spyne usa) e adicionamos `find_spec`
(+ create_module/exec_module) à CLASSE do importador embutido. Assim o próprio
mecanismo do six — que já sabe resolver os submódulos aninhados — volta a
funcionar nativamente no Python 3.12+, sem gambiarra de redirecionamento.

No Python 3.13, o módulo padrão `cgi` foi removido. O spyne ainda usa apenas
`cgi.parse_header` no caminho SOAP/WSGI, então registramos um substituto mínimo
baseado em `email.message.Message` quando o módulo não existe.

Basta `import common.spyne_py312_fix` ANTES de importar o spyne.
"""
import importlib.util
import os
import sys
import types
from email.message import Message
from importlib.machinery import ModuleSpec
from importlib.machinery import SourceFileLoader

_PKG = "spyne.util.six"


def _patch_cgi_removido():
    if "cgi" in sys.modules:
        return
    if importlib.util.find_spec("cgi") is not None:
        return

    cgi = types.ModuleType("cgi")

    def parse_header(line):
        msg = Message()
        msg["content-type"] = line
        value = msg.get_content_type()
        params = dict(msg.get_params()[1:])
        return value, params

    cgi.parse_header = parse_header
    sys.modules["cgi"] = cgi


def _carregar_six_embutido():
    if _PKG in sys.modules:
        return sys.modules[_PKG]
    spec = importlib.util.find_spec("spyne")  # localiza sem executar __init__
    spyne_dir = spec.submodule_search_locations[0]
    six_path = os.path.join(spyne_dir, "util", "six.py")
    loader = SourceFileLoader(_PKG, six_path)
    six_spec = importlib.util.spec_from_loader(_PKG, loader)
    mod = importlib.util.module_from_spec(six_spec)
    sys.modules[_PKG] = mod
    loader.exec_module(mod)
    return mod


def _patch_importer(six_mod):
    importer = getattr(six_mod, "_importer", None)
    if importer is None:
        return
    cls = type(importer)
    if getattr(cls, "_py312_patched", False):
        return

    def find_spec(self, fullname, path=None, target=None):
        if self.find_module(fullname, path) is None:
            return None
        return ModuleSpec(fullname, self)

    def create_module(self, spec):
        return self.load_module(spec.name)

    def exec_module(self, module):
        pass

    cls.find_spec = find_spec
    cls.create_module = create_module
    cls.exec_module = exec_module
    cls._py312_patched = True


_patch_cgi_removido()
_six = _carregar_six_embutido()
_patch_importer(_six)
