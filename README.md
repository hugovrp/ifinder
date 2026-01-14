# IFINDER

O **IFinder** é um assistente virtual inteligente desenvolvido para o IF Sudeste MG - Campus Barbacena. Ele utiliza Inteligência Artificial para facilitar o acesso à informação, ajudando alunos, servidores e a comunidade a encontrar notícias, editais, contatos e documentos no portal oficial da instituição.

## Sobre

O projeto atua como um agente autônomo capaz de navegar pelo site do instituto, ler documentos e responder perguntas em linguagem natural. Diferente de uma busca comum, o IFinder entende o contexto da pergunta e seleciona a melhor ferramenta para buscar a resposta, seja lendo uma notícia recente, acessando o calendário acadêmico em PDF ou buscando informações sobre o corpo docente.

Principais funcionalidades:
- **Busca de Notícias:** Retorna os destaques mais recentes do campus.
- **Leitura de Documentos:** Capaz de ler e interpretar editais, calendários e cardápios em formato PDF.
- **Navegação Inteligente:** Acessa páginas específicas (Corpo Docente, Fale Conosco) e extrai informações relevantes.
- **Filtro de Informação:** Prioriza fontes oficiais e links diretos para garantir precisão.

## Como inicializar

Siga os passos abaixo para rodar o projeto localmente:

### Pré-requisitos
- Python 3.10 ou superior
- Navegador Google Chrome instalado (para uso do Selenium)
- Chave de API do Google Gemini

### Instalação

1. Clone o repositório e entre na pasta do projeto:
   ```bash
   cd ifinder/backend
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na pasta `backend`.
   - Adicione suas chaves de API:
     ```
     GOOGLE_API_KEY=sua_chave_aqui
     SUMMARIZER_API_KEY=sua_chave_aqui
     ```

### Executando

Para iniciar o servidor backend:

```bash
python main.py
```

O servidor estará rodando em `http://localhost:5050` e a interface pode ser acessada pelo navegador.

## Tecnologias

O projeto foi construído utilizando:

- **Linguagem:** Python 3
- **Framework Web:** Flask
- **IA & Agentes:** 
  - [Agno](https://github.com/agno-agi/agno) (Framework de Agentes)
  - Google Gemini (Modelo de Linguagem)
- **Automação & Web Scraping:**
  - Selenium (Navegação em páginas dinâmicas)
  - BeautifulSoup4 (Parsing de HTML)
  - PyMuPDF (Leitura de PDFs)
- **Banco de Dados:** SQLite (Armazenamento de sessões)