# Validação no PVA

Valida no programa validador da Receita Federal (PVA) os arquivos do SPED que os módulos
deste repositório geram. O PVA é o juiz: zero erro no PVA, com o relatório guardado, é o
que vale. O conferidor estático só adianta o que é estrutura.

O workflow `.github/workflows/pva.yml` roda no runner próprio da KMEE (rótulo
`kmee-l10n-br`) e nunca em pull request de fork:

- à mão (`workflow_dispatch`), escolhendo a série e as escriturações;
- em pull request deste repositório com o rótulo `pva`;
- toda noite, nas séries 16.0 e 18.0.

O `.github/workflows/confere.yml` roda no Actions hospedado em todo pull request que
toca um módulo de escrituração: gera os arquivos da EFD e roda só o conferidor estático.

## O que tem aqui

| Arquivo                                   | O que é                                                                                                                                                                                                                                                                              |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `cenarios/test_zz_pva.py`                 | cenários da EFD ICMS/IPI (presumido, com 0015, com devolução) e da EFD Contribuições (presumido, lucro real em outubro e novembro), da série desta branch                                                                                                                            |
| `gerar.sh`                                | gera os arquivos dentro da imagem `oca-ci` da série: copia o cenário para os testes do `l10n_br_sped_efd_icms_ipi` (só no checkout do CI, nunca no commit) e roda os testes dos cenários; a ECD e a ECF saem dos testes dos próprios módulos (`ECD_GERAR_ARQUIVO`, `ECF_GERAR_DEMO`) |
| `confere.sh`, `confere.py`                | conferidor estático contra o leiaute que o `sped-extractor` extraiu do descritor do PVA                                                                                                                                                                                              |
| `instaladores.csv`                        | versão, endereço oficial e SHA256 do instalador de cada PVA                                                                                                                                                                                                                          |
| `Dockerfile`, `fix_arial.py`, `imagem.sh` | imagem do PVA, construída no runner a partir do instalador oficial e guardada só ali                                                                                                                                                                                                 |
| `pva_driver.py`                           | importa, valida e salva o relatório no PVA, sem gerenciador de janelas                                                                                                                                                                                                               |
| `validar.sh`                              | um container sem rede por arquivo, com o driver                                                                                                                                                                                                                                      |
| `resumo.py`, `esperados.csv`              | resume os relatórios e reprova o que não estiver na lista de esperados                                                                                                                                                                                                               |

## Rodar fora do CI

Precisa de Docker numa máquina x86_64 (em Mac ARM,
`DOCKER_DEFAULT_PLATFORM=linux/amd64`, bem mais lento). Os nomes de container levam o
prefixo de `PVA_PREFIXO`.

```sh
# dentro da imagem oca-ci da série, com um PostgreSQL ao lado
tools/pva/gerar.sh /tmp/pva/arquivos efd_icms_ipi,ecd
tools/pva/confere.sh /tmp/pva/arquivos
# na máquina com Docker
PVA_PREFIXO=meu-projeto-pva tools/pva/validar.sh /tmp/pva/arquivos /tmp/pva/relatorios
python3 -I tools/pva/resumo.py /tmp/pva/relatorios /tmp/pva/arquivos
```

## Como a automação funciona

O PVA é uma aplicação Swing e o container não tem gerenciador de janelas. O
`pva_driver.py` espera cada janela pelo título (`xdotool search`), responde os diálogos
de pergunta com Enter (botão padrão: Sim ou Ok), cancela a atualização de tabelas com
Esc e clica em coordenadas só onde não há janela própria: menus da janela principal,
caixas do relatório e os diálogos que a ECF desenha dentro da janela principal (campos
de transporte: Não; linhas desprezadas na importação: Sim, para guardar o relatório de
importação). A tela tem sempre 1280x1024 e a janela principal de cada PVA abre sempre no
mesmo lugar. Cada passo deixa uma captura de tela no artefato.

O container roda sem rede, então o PVA não atualiza as tabelas oficiais (é como foram as
validações manuais de referência). Para atualizar, rode à mão com "atualizar_tabelas".

## Quando sai versão nova de um PVA

1. Baixe o instalador Linux na página da Receita, confira e troque a linha em
   `instaladores.csv` (versão, endereço e `sha256sum`). A imagem nova é construída na
   próxima rodada; a antiga é apagada.
2. Rode o workflow à mão. Se a automação se perder, o artefato tem a tela em que parou:
   ajuste em `pva_driver.py` o título do diálogo ou a coordenada (tabela `KINDS`).
3. Mensagem nova no relatório: corrija o gerador ou, se for esperada (dado que o cenário
   não tem, como a ECD do ano anterior), acrescente a linha em `esperados.csv` com o
   motivo.
4. Leiaute novo: o conferidor lê o leiaute do `sped-extractor` fixado por commit em
   `confere.sh`; aponte para o commit que tiver o leiaute novo.
