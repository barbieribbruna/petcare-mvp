# PetCare MVP

Sistema web responsivo para tutores de animais registrarem e consultarem a saúde de seus pets (vacinas, consultas, medicamentos e exames).

Projeto individual da disciplina Projeto de Software (ADS).

## Status

Em desenvolvimento. O andamento de cada requisito está no quadro abaixo.

## Requisitos

| Código | Descrição | Prioridade | Status |
|---|---|---|---|
| RF01 | Autenticação de usuário | Obrigatório | Implementado e testado (pytest) |
| RF02 | Cadastro de pets | Obrigatório | Planejado |
| RF03 | Registro de saúde | Obrigatório | Planejado |
| RF04 | Histórico de saúde | Desejável | Planejado |

Requisitos não funcionais: segurança e privacidade (RNF01, RNF02), desempenho e portabilidade (RNF03) e acessibilidade (RNF04).

## Tecnologias

Python 3.12, Flask 3.1, SQLAlchemy 2.0 e SQLite, em arquitetura monolítica de três camadas (apresentação, regras de negócio e persistência).

## Fora do escopo do MVP

Integração com clínicas, notificações automáticas e inteligência artificial.

## Como executar

Passos para Windows PowerShell, na raiz do repositório:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Chave da sessão: use um valor longo e aleatório, por exemplo o gerado por
# python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:PETCARE_SECRET_KEY = "cole-aqui-a-chave-gerada"

# Apenas para teste local por http (sem HTTPS). Não use em produção.
$env:PETCARE_COOKIE_SECURE = "0"

python run.py
```

Depois, acesse http://127.0.0.1:5000 no navegador.

Para rodar os testes automatizados:

```powershell
python -m pytest -v
```

## Limitações conhecidas

- O bloqueio após 5 tentativas de login inválidas é guardado em memória: zera ao reiniciar o servidor e não vale entre processos.
- O SQLite é adequado apenas ao volume de dados do MVP.
- HTTPS não está configurado no ambiente local.
- Desempenho (RNF03) e acessibilidade (RNF04) ainda não foram medidos nem testados com usuários.

## Fluxo de trabalho

Commits semânticos (feat, fix, test, docs, chore) e Pull Requests com auto-revisão.
