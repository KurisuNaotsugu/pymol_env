# (pymol plugin) pymol_feature_paintor

## プロジェクト概要

　本プロジェクトはオープンソースの分子構造グラフィクツールであるpymolのプラグインとして開発され、pymol上に表示されているタンパク質3Dモデルに対して、指定領域ごとの着色を施す機能を付与します。また、領域指定はcsvファイルによる指定およびUniprot APIから取得した feature 情報から指定することが可能です。3D構造データは AlphaFold DB から uniprotアクセッション番号をキーとして自動的にロードすることも可能です。

Uniprotのトポロジー情報に基づいて着色されたタンパク質構造

## 主な機能

### 1. 3D構造データのロード (Alphahold DB API)

- Alphahold DB API () からuniprot開くセッション番号をキーにして構造データ取得
- pymol上に描画する

### 2. 指定領域の着色

- 指定したフォーマットのCSVファイルの情報に従って、構造データの指定領域を着色
- Uniprotアクセッション番号をキーに Uniprot から feature 情報 (二次構造情報やドメイン情報) を取得
- 指定した feature 情報の領域情報に従って構造データの指定領域を着色

### 3.  補助機能

- Alphafold DB API および Uniprot から取得した feature 情報に含まれれるアミノ酸配列の整合確認機能 (配列不一致による領域指定のズレ防止)
- 登録した feature 情報には固有の色が与えられて描写される (auto color fill)

## 想定用途

- PyMOL で AlphaFold DB の構造を素早く可視化したい
- 膜貫通領域や細胞外ドメインなどのトポロジー情報を可視化したい
- ドメインスワップなどを実施した領域を視覚的に把握したい

## セットアップ

### 1. 実行環境

　適当なパッケージ管理ツールおよび仮想環境管理ツールを使用して、オープンソース版のpymolが実行できる仮想環境を構築してください。環境構築に特段のこだわりがない場合にはconda環境での構築が最も簡単です。

- Python: `>= 3.11`

### 2. PYTHONPATHの設定

　リポジトリの `src` **ディレクトリの絶対パス**を、`PYTHONPATH` としてその環境に登録します。これで `from api...` などが PyMOL 内の Python から解決されます。

```bash
conda activate env_name
conda env config vars set PYTHONPATH=/path/to/pymol_env/src
conda deactivate
conda activate env_name
```

`/path/to/pymol_env` は自分のクローンに置き換えてください（例: macOS では `$HOME/pymol_env/src`）。

**poetry環境の場合はプロジェクト直下**`.env`を置き、`PYTHONPATH=...` を記述してください

### 3. .pymolrcのセットアップ

　PyMOL は起動時に **ホームディレクトリの** `~/.pymolrc` を読み、記述されたコマンドを実行します。ホームディレクトリに下記を記述した `.pymolrc` を設置することで、毎回プラグインで使用するコマンドの登録作業を省略することができます。

例（パスは環境に合わせて**絶対パス**に置き換え）:

```text
run /Users/you/pymol_env/src/plugin/fetch_af_structure.py
run /Users/you/pymol_env/src/plugin/paint_feature.py
```

※ `.pymolrc` を設置しない場合は、上記コマンドを毎回pymolコンソール上に入力して実行してください

**※** `.pymolrc` は**上記の** `PYTHONPATH` **の追加後に実施してください**

## リポジトリ構成

```
pymol_env/
├── pyproject.toml
├── README.md
├── src/
│   ├── api/                     # AlphaFold / UniProt の APIを直接叩く層
│   ├── core/                    # models, http, cache, api_response_validation など
│   ├── services/                # APIを叩いて取得したresponseをパースして情報を抽出する層
│   ├── converter/               # servise層で抽出したデータをさらに集計して、molpaintで使用するデータクラスへ変換する層
│   ├── molpaint/                # pymolへのfeature情報の登録や構造取得、着色を実行するためのコマンド群
│   └── plugin/                  # PyMOL から `run` するエントリ
│       ├── fetch_af_structure.py  # `fetch_af` を登録
│       ├── paint_feature.py       # `register_*` / `paint_feature`
│       └── plugin_test.py         # `hello_pymol`（プラグインテスト用）
└── tests/                       # CLI 手動テスト（ネットワーク参照）
```

`pyproject.toml` の `[tool.poetry.packages]` では `src` 直下の `api`, `core`, `services`, `converter`, `molpaint`, `plugin` をパッケージとして登録しています。

## 使い方

### 1. PyMOL の起動とプラグインのインポート

1. プロジェクトのルートディレクトリに移動

```bash
cd /path/to/pymol_env
```

1. 仮想環境をアクチベート (`conda activate` or `poetry shell`)

```bash
conda activate env_name # conda環境
poetry shell # poetry環境
```

1. **pymol 起動**

```bash
pymol
```

pymolが起動して、プラグインのスクリプトがpymolのコマンドライン上で実行されていれば成功です

プラグイン読み込み成功時のpymolの画面

### 2. AlphaFold 構造を取得してロード

##### コマンド

```python
fetch_af P12345
```

##### 引数
```text 
  accession (str): UniProt accession（例: P12345）
```

#### Notes
- ロードされる PyMOL オブジェクト名は `AF_{accession}` になります。
- 初回取得時はキャッシュ（例: `~/.cache/pymol_topology/...`）へ保存し、2回目以降は再利用します。

![ロードされた3D構造データ]()

#### 2. UniProt からfeature 情報を登録
##### コマンド
```python
preview_feature_domains_from_accession P12345
```
##### 引数
```text 
  accession (str): UniProt accession（例: P12345）
```

![Uniprtoから取得できるfeature一覧]()

#### 3. 着色する feature を pymol に登録
##### コマンド
```python
register_feature_domain_subset rg_P12345, Transmembrane, Helical
```
##### 引数
```text 
  registry_name: レジストリキー (例: rg_P12345)
  domain_name (str): ドメイン名 (例: Topological, Transmenbrane)
  description (str): ドメインの詳細　 (例: Helical, Extracelluer)
```

#### Note
一覧に出た文字列と **完全一致** する条件で絞り込み登録します（`domain_name` のみ、`description` のみ、または両方＝AND）。いずれか一方は必須です。

#### 3. csvファイルから feature 情報を登録
##### コマンド
```python
register_feature_from_csv rg_P12345, /path/to/regions.csv
```
##### 引数
```text 
  registry_name: レジストリキー (例: rg_P12345)
  path (str): csvファイルまでのパス
```

#### 4. 3D構造データの着色
##### コマンド
```python
paint_feature rg_P12345, AF_P12345
```
##### 引数
```text 
  registry_name: レジストリキー (例: rg_P12345)
  object_name (str): pymolオブジェクト (例: AF_P12345)
```
#### Note
対象オブジェクトが未ロードの場合はエラーになります（自動では AlphaFold を取得しません）。

![着色後の3D構造データ]()

#### 5. 登録済みの feature 情報の閲覧
##### コマンド
```python
list_feature_registry
```
![登録済みの featuer 情報一覧の出力]()

#### 6. 登録済みの feature の指定領域の閲覧
##### コマンド
```python
show_feature_domain_infos rg_P12345
```

#### 引数
```text 
  registry_name: レジストリキー (例: rg_P12345)
```

### 主要データクラス（どこで使うか）

- `ApiResponse`（`src/api/base.py`）
  - 形: `status_code: int`, `headers: dict[str, str]`, `body: Any`, `raw_text: str`
  - 用途: `src/api` の戻り値として統一し、`src/services` が `body` を解釈
- `StructureArtifact`（`src/core/models.py`）
  - 形: `accession`, `format`, `local_path`, `source_url`, `checksum?`
  - 用途: `AlphaFoldDBFetcherClient`（`src/api/alphafold.py`）の `fetch_structure()` の成果物（PyMOL load の入力）
- `AminoAcidSequence`（`src/core/models.py`）
  - 形: `value: str`（`normalized` / `matches()` を提供）
  - 用途: AlphaFold と UniProt の配列比較に共通利用
- `SequenceValidationResult`（`src/services/sequence_validation.py`）
  - 形: `match`, `af_sequence`, `uniprot_sequence`, `message`
  - 用途: 配列一致検証の結果を UI/CLI/PyMOL 側へ返す
- `DomainInfo`（`src/converter/constractor.py`）
  - 形: `domain_name`, `spans`（複数区間可）, `chain?`, `color?`（`ColorDef`）
  - 用途: トポロジー領域の標準表現。`DomainInfoFactory` が UniProt features から生成し、`DomainColorScheme().color_fill(リスト)` で一覧に重複のない色名を付与
- `ColorDef` / `DomainColorScheme`（`src/converter/constractor.py`）
  - 形: `ColorDef` は主に PyMOL の**色名**（`name`）。`DomainColorScheme.color_fill` が `list[DomainInfo]` にパレット色を割り当て
  - 用途: 着色前に `DomainColorScheme.color_fill` でリスト単位で埋め（色名は一覧内で重複しない）、`Painter` は `ColorDef.name` をそのまま `cmd.color` に渡す

## データ形式と流れ
### 構造取得

#### 1) API 呼び出し

- `AlphafoldApiClient.get_prediction(accession) -> ApiResponse`
- `ApiResponse.body` は AlphaFold の JSON（`dict` または `list[dict]`）を保持

#### 2) URL 抽出・形式決定

- `AlphaFoldDBClient`（`services/alphafold_extractor.py`）`pick_structure_url(resp, accession) -> tuple[url: str, fmt: str]`
- `fmt` は既定優先順 `("cif", "pdb", "bcif")`

#### 3) 取得成果物へ変換

- `AlphaFoldDBFetcherClient`（`src/api/alphafold.py`）`fetch_structure(...) -> StructureArtifact`
- `StructureArtifact.local_path` は実ファイルの保存先を指す

#### 4) PyMOL 適用

- `src/plugin/fetch_af_structure.py` の `fetch_af` が `cmd.load(str(artifact.local_path), ...)` を実行

キャッシュ保存先:

- ベース: `~/.cache/pymol_topology`
- サブ: `alphafold`
- ファイル名: `AF_{accession}.{cif|pdb|bcif}`

### 配列検証

1. AlphaFold 側:
  - `ApiResponse.body` から `uniprotSequence`（または `sequence`）を抽出
  - `AminoAcidSequence` へ変換
2. UniProt 側:
  - `UniprotApiClients.get_search_response(accession) -> ApiResponse`（`fields` は付けず、必要な情報は `body` から抽出）
  - `UniprotExtractor.extract_sequence(...) -> AminoAcidSequence`
3. 比較:
  - `validate_sequence(af_sequence, uniprot_sequence) -> SequenceValidationResult`
  - `match` と `message` を PyMOL/CLI に表示

### トポロジー着色

1. `UniprotApiClients.get_search_response(accession) -> ApiResponse` で UniProt を取得し、`domain_infos_from_response(resp, accession=..., config=..., chain=...)`（`src/converter/pipeline.py`）で `list[DomainInfo]` を得る（PyMOL の `preview_feature_domains_from_accession` / `register_feature_domain_subset` はこの流れをラップしている）


2. 抽出: `UniprotExtractor.extract_features(resp, accession=...) -> list[UniprotFeatures]`
  - 各 `UniprotFeatures` は 1 件の feature について `feature`（型名）・`location`・`description` を保持する
3. 成形: `DomainInfoFactory.extract_features(list[UniprotFeatures]) -> list[DomainInfo]`
  - 同一 `description` ごとにまとめた `DomainInfo`（`domain_name` は feature type、`description` は下位ラベル）
4. 色付与: `DomainColorScheme().color_fill(list[DomainInfo])` で未設定分に `palette`（既定は `converter.color_palette.EXTRA_PYMOL_COLOR_NAMES`）を順に割り当て（一覧内で色名が重複しない）
5. PyMOL 適用: `Painter.paint_domaininfo(cmd, object_name, domaininfo)` が `domaininfo.spans` から selection を組み立て、各 span に `cmd.color(color_name, selection)` を実行（`domaininfo` は 1 件ずつ）

