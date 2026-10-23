"""Ferramentas de memória de longo prazo para projetos de arquitetura Cloud.

O Store localiza cada item por namespace (tupla) e chave (string):

- projeto: namespace ("consultor-arquitetura-cloud", "ana", "projects"),
  chave "plataforma aurora", valor {"nome": "Plataforma Aurora"};
- decisão: namespace ("consultor-arquitetura-cloud", "ana", "decisions", "plataforma aurora"),
  chave única, valor {"texto": "Usar AWS na região sa-east-1"}.

Os namespaces de projetos e decisões são separados para a listagem de projetos
não incluir decisões. A aplicação normaliza o nome do projeto com ``casefold()``.
"""

import json
from dataclasses import dataclass
from uuid import uuid4

from langchain.tools import ToolRuntime, tool


@dataclass
class AgentContext:
    """Identidade escolhida pela aplicação web para uma execução do agente.

    Attributes:
        user_id: Identificador do perfil selecionado na página.
    """

    user_id: str


@tool
def listar_projetos(runtime: ToolRuntime[AgentContext]) -> str:
    """Liste os projetos do usuário atual.

    Args:
        runtime: Contexto fornecido pelo LangChain com o usuário e o Store.
    """
    store = runtime.store
    assert store is not None
    namespace = ("consultor-arquitetura-cloud", runtime.context.user_id, "projects")
    projects = [item.value["nome"] for item in store.search(namespace, limit=100)]
    return json.dumps(projects, ensure_ascii=False)


@tool
def criar_projeto(nome: str, runtime: ToolRuntime[AgentContext]) -> str:
    """Crie um projeto com o nome informado pelo usuário.

    Args:
        nome: Nome do novo projeto.
        runtime: Contexto fornecido pelo LangChain com o usuário e o Store.
    """
    store = runtime.store
    assert store is not None
    name = nome.strip()
    if not name:
        return "Informe um nome para o projeto."

    namespace = ("consultor-arquitetura-cloud", runtime.context.user_id, "projects")
    key = name.casefold()
    if store.get(namespace, key) is not None:
        return "Já existe um projeto com esse nome. Liste os projetos e escolha o existente."

    project = {"nome": name}
    store.put(namespace, key, project)
    return json.dumps(project, ensure_ascii=False)


@tool
def consultar_projeto(nome_projeto: str, runtime: ToolRuntime[AgentContext]) -> str:
    """Consulte as decisões registradas para um projeto do usuário atual.

    Args:
        nome_projeto: Nome do projeto a consultar.
        runtime: Contexto fornecido pelo LangChain com o usuário e o Store.
    """
    store = runtime.store
    assert store is not None
    user_id = runtime.context.user_id
    project_key = nome_projeto.strip().casefold()
    project_namespace = ("consultor-arquitetura-cloud", user_id, "projects")
    project = store.get(project_namespace, project_key)
    if project is None:
        return "Projeto não encontrado para este usuário."

    decisions_namespace = ("consultor-arquitetura-cloud", user_id, "decisions", project_key)
    decisions = [item.value["texto"] for item in store.search(decisions_namespace, limit=100)]
    return json.dumps({"nome": project.value["nome"], "decisoes": decisions}, ensure_ascii=False)


@tool
def registrar_decisao(
    nome_projeto: str,
    decisao: str,
    runtime: ToolRuntime[AgentContext],
) -> str:
    """Registre uma decisão aceita pelo usuário como um item próprio do Store.

    Args:
        nome_projeto: Nome do projeto que receberá a decisão.
        decisao: Escolha aceita pelo usuário, em uma frase.
        runtime: Contexto fornecido pelo LangChain com o usuário e o Store.
    """
    store = runtime.store
    assert store is not None
    user_id = runtime.context.user_id
    project_key = nome_projeto.strip().casefold()
    project_namespace = ("consultor-arquitetura-cloud", user_id, "projects")
    if store.get(project_namespace, project_key) is None:
        return "Projeto não encontrado para este usuário."
    if not decisao.strip():
        return "Informe a decisão a registrar."

    decisions_namespace = ("consultor-arquitetura-cloud", user_id, "decisions", project_key)
    # Uma chave nova cria um item novo; as decisões anteriores continuam no Store.
    value = {"texto": decisao.strip()}
    decision_id = str(uuid4())
    store.put(decisions_namespace, decision_id, value)
    return json.dumps({"id": decision_id, **value}, ensure_ascii=False)


TOOLS = [listar_projetos, criar_projeto, consultar_projeto, registrar_decisao]
