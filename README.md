# Extrator de Dados para Excel

Base funcional para consultar dados, normalizá-los e manter uma planilha Excel sem duplicações.

## Teste completo com API local

1. Crie e ative um ambiente virtual: `python -m venv .venv` e `.\.venv\Scripts\Activate.ps1`.
2. Instale as dependências: `python -m pip install -r requirements.txt`.
3. Copie `.env.example` para `.env`. Para usar a API local, preencha o `.env` conforme o arquivo já criado neste projeto.
4. Em um terminal, inicie a API: `python -m src.demo_api`.
5. Em outro terminal, execute o extrator: `python -m src.main --once`.

O comando cria `output/dados_gerenciador.xlsx` com dois registros iniciais. Na segunda execução, não duplica as linhas.

Para simular um registro novo, com a API local em execução, rode no PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/records -Headers @{ Authorization = 'Bearer demo-token' } -ContentType 'application/json' -Body '{"id":"1003","nome":"Carla Alves","status":"Ativo","valor":950.00}'
```

Execute novamente `python -m src.main --once`. Apenas o registro `1003`, criado após o marcador salvo, será consultado e inserido na planilha. Para simular uma alteração, envie outro `POST` com o mesmo `id`; a linha correspondente será atualizada.

### Simulação de notas fiscais

A API local cria automaticamente 10 notas fiscais novas a cada minuto. Cada nota possui `id`, `numero_nota`, `serie`, `emitente`, `cnpj_emitente`, `valor_total`, `status` e `updated_at` em horário de Brasília. Os controles ficam no `.env`:

```env
DEMO_BATCH_INTERVAL_SECONDS=60
DEMO_BATCH_SIZE=10
```

Com o extrator em `SCHEDULE_MODE=loop`, cada lote novo é inserido automaticamente no Excel na próxima verificação.

## Atualização automática

Para manter o processo ativo, use `SCHEDULE_MODE=loop` e defina `SYNC_INTERVAL_SECONDS` no `.env` (por exemplo, `600` para verificar a cada 10 minutos). Depois execute `python -m src.main` e mantenha o processo em execução. Para interromper, use `Ctrl+C`.

No ambiente de demonstração deste projeto, o intervalo configurado é de 10 segundos para tornar a atualização visível rapidamente. Para uso normal, aumente-o para um valor adequado, como `600`.

Em cada ciclo, o script lê `state/sync_state.json`, que guarda o maior valor de `UPDATED_AT_FIELD` recebido com sucesso. Se `API_UPDATED_SINCE_PARAM` estiver preenchido com o nome confirmado do filtro da API, esse marcador é enviado na consulta. Portanto, a API devolve apenas os registros posteriores à última sincronização; o Excel ainda compara o ID para impedir duplicação e atualizar um registro já existente, se a API também retornar alterações.

## Fuso horário

Todos os horários do modo de demonstração usam `America/Sao_Paulo` (horário de Brasília, UTC−03:00). O estado de sincronização é salvo com o offset `-03:00`; no Excel, datas e horas são exibidas como `dd/mm/aaaa hh:mm` em horário de Brasília. Timestamps recebidos em UTC também são convertidos antes de serem exibidos e comparados.

Para iniciar automaticamente após reinicializações do Windows, configure o Agendador de Tarefas para executar `python -m src.main` ao entrar no Windows. O processo deve ser iniciado na pasta deste projeto e usar o Python/ambiente virtual correto.

## Como conectar à API real

Altere `DATA_SOURCE=api` e preencha no `.env` somente informações confirmadas pela documentação:

- `API_BASE_URL`, `API_ENDPOINT` e credencial;
- `API_RECORDS_PATH`, se os registros não vierem como lista na raiz do JSON;
- campos `RECORD_ID_FIELD` e `UPDATED_AT_FIELD`;
- parâmetros de data e paginação, se a API os suportar.

O cliente usa apenas os parâmetros cujo nome foi preenchido. Ele não presume endpoint, formato de resposta nem paginação. Uma resposta de registros deve conter uma lista de objetos JSON, no caminho configurado.

## Sincronização

Após exportar com sucesso, o script registra um horário UTC em `state/sync_state.json`. Na próxima execução, ele envia esse valor à API apenas se `API_UPDATED_SINCE_PARAM` estiver configurado. A planilha também compara registros pelo identificador único: novos são inseridos, registros alterados são atualizados e idênticos são ignorados.

## Testes

Instale também `pytest` (`python -m pip install pytest`) e execute `python -m pytest`.

## Limitação conhecida

Sem a documentação da API, o modo `api` não pode ser validado. O modo `mock` valida localmente a exportação, formatação, deduplicação e atualização incremental. Se a API não oferecer filtro por data de atualização, o script buscará os dados disponíveis e fará a deduplicação local; isso é seguro, mas menos eficiente.
