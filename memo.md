# dlt の内部構造

## Pipeline.run
`data` 引数から、`destination` で指定された出力先の `dataset_name` で指定されたデータセットにデータをロードします。

### 注:
このメソッドは、`data` 引数からデータを `extract` し、スキーマを推論し、
データをロードパッケージ（テーブルを表す jsonl または PARQUET ファイル）に `normalize` し、
それらのパッケージを `destination` に `load` します。

`data` は複数の形式で提供できます。
* JSON シリアル化可能なオブジェクトの `list` または `Iterable` 
    例: `dlt.run([1, 2, 3], table_name="numbers")`
* 任意の `Iterator` または (`Generator`) を生成する関数 
    例: `dlt.run(range(1, 10), table_name="range")`
* @dlt.resource で修飾された関数または関数のリスト 
    例: `dlt.run([chess_players(title="GM"), chess_games()])`
* @dlt.source で修飾された関数または関数のリスト。

`dlt` は `bytes`、`datetime`、`decimal`、`uuid` オブジェクトを扱うため、
バイナリデータや日付などを含むドキュメントを自由にロードできます。

### 実行:
`run` メソッドはまず `sync_destination` メソッドを使用して、
パイプラインの状態とスキーマを出力先と同期します。
この動作は `restore_from_destination` 設定オプションで無効にできます。

次に、前のデータが完全に処理されていることを確認します。処理されていない場合、
`run` メソッドは正規化し、保留中のデータ項目をロードして **終了** します。

保留中のデータがない場合、`data` 引数から新しいデータが抽出され、正規化されてロードされます。

### 引数:
*  `data` (Any): 
出力先にロードするデータ

* `destination`(TDestinationReferenceArg、オプション): 
    dlt がデータをロードする出力先の名前、または `dlt.destination` からインポートした出力先モジュール。
    指定されていない場合は、`dlt.pipeline` に渡された値が使用されます。

* `staging` (TDestinationReferenceArg、オプション): 
    dlt がデータを出力先にロードする前に一時的にロードするステージング出力先の名前。
    `dlt.destination` からインポートしたモジュールも使用できます。

* `dataset_name` (str、オプション): 
    データをロードするデータセットの名前。
    データセットとは、テーブルの論理的なグループ（リレーショナルデータベースの `schema` など）または多数のファイルをグループ化したフォルダです。
    指定されていない場合は、`dlt.pipeline` に渡された値が使用されます。指定されていない場合は、デフォルトで `pipeline_name` が使用されます。

* `credentials` (Any、オプション): 
    `destination` の認証情報（データベース接続文字列または Google の辞書など）クラウド認証情報。
    ほとんどの場合、None に設定する必要があります。
    これにより、`dlt` は `secrets.toml` または環境変数を使用して正しい認証情報を推測します。

* `table_name` (str, オプション): `dataset` 内でデータをロードするテーブル名。
    この引数は、`data` がリスト/反復可能オブジェクトまたは `__name__` 属性を持たない反復子である場合に必須です。
    この引数の動作は、`data` の型によって異なります。
    * ジェネレータ関数 - 関数名がテーブル名として使用されます。
        `table_name` はこのデフォルトをオーバーライドします。
    * `@dlt.resource` - リソースには完全なテーブルスキーマが含まれており、テーブル名も含まれています。
        `table_name` はこのプロパティをオーバーライドします。使用には注意が必要です。
    * `@dlt.source` - ソースには、それぞれテーブルスキーマを持つ複数のリソースが含まれています。
        `table_name` はソース内のすべてのテーブル名をオーバーライドし、データを単一のテーブルにロードします。

* `write_disposition` (TWriteDispositionConfig, オプション): 
    テーブルにデータを書き込む方法を制御します。
    短縮文字列リテラルまたは設定辞書を指定できます。
    * 使用可能な短縮文字列リテラル：
        `append` は常にテーブルの末尾に新しいデータを追加します。
        `replace` は既存のデータを新しいデータで置き換えます。
        `skip` はデータの読み込みを禁止します。
        `merge` は "primary_key" と "merge_key" のヒントに基づいてデータの重複排除とマージを行います。
        デフォルトは "append" です。
    * 書き込み動作は設定辞書によってさらにカスタマイズできます。
        例えば、SCD2 テーブルを取得するには、`write_disposition={"disposition": "merge", "strategy": "scd2"}` を指定します。
    * `dlt.resource` の場合はテーブルスキーマ値が上書きされ、`dlt.source` の場合はすべてのリソースの値が上書きされることに注意してください。

* `columns` (TAnySchemaColumns、オプション): 
    列スキーマのリスト。
    列名、データ型、書き込み処理、パフォーマンスヒントを記述した型付き辞書で、作成されたスキーマを完全に制御できます。

* `primary_key` (TColumnNames, オプション): 
    秘密キーを構成する列名または列名のリスト。
    通常、ロードされたデータの重複を排除するために、"merge" 書き込み処理と組み合わせて使用​​されます。

* `schema` (Schema, オプション): 
    すべてのテーブルスキーマをグループ化する明示的な `Schema` オブジェクト。
    デフォルトでは、`dlt` は（`data` 引数で渡された場合は）ソースからスキーマを取得するか、デフォルトのスキーマを独自に作成します。

* `loader_file_format` (TLoaderFileFormat, オプション): 
    ローダーがロードパッケージの作成に使用するファイル形式。
    すべての file_format がすべての出力先と互換性があるわけではありません。
    デフォルトでは、選択した出力先の推奨ファイル形式が使用されます。

* `table_format` (TTableFormat, オプション):
    「delta」または「iceberg」を指定できます。
    出力先がテーブルを保存するために使用するテーブル形式です。
    現在、ファイルシステムと Athena の出力先でテーブル形式を選択できます。

* `schema_contract` (TSchemaContract, オプション): 
    スキーマコントラクト設定をオーバーライドすると、スキーマ内のすべてのテーブルのスキーマコントラクト設定が置き換えられます。
    デフォルトは None です。

* `refresh` (TRefreshMode, オプション): 
    今回の実行で新しいデータをロードする前に、ソースを完全にまたは部分的にリセットします。
    以下の更新モードがサポートされています。
    * `drop_sources` - 
        パイプラインの `run` または `extract` メソッドで現在処理中のすべてのソースのテーブルとソースおよびリソースの状態を削除します。
        (注: スキーマ履歴は消去されます)
    * `drop_resources` - 
        処理中のすべてのリソースのテーブルとリソースの状態を削除します。
        ソースレベルの状態は変更されません。(注: スキーマ履歴は消去されます)
    * `drop_data` - 
        処理中のすべてのリソースのデータとリソースの状態をすべて消去します。
        スキーマは変更されません。

## Pipeline.activate
パイプラインをアクティブ化します。

アクティブなパイプラインは、複数の `dlt` コンポーネントのコンテキストとして使用されます。
`pipeline.run` メソッドと `pipeline.extract` メソッドの外部で評価されるソースとリソースに状態を提供します。
たとえば、使用するソースが `dlt.source` デコレートされた関数内の状態にアクセスしている場合、その状態はアクティブなパイプラインによって提供されます。

アクティブなパイプラインの名前は、値の検索時にオプションの最外部セクションとしてシークレットと構成値を解決する際に使用されます。
たとえば、`chess_pipeline` という名前のパイプラインがアクティブで、`dlt` が `BigQuery` 構成を検索する場合、
最初に `chess_pipeline.destination.bigquery.credentials` を検索し、次に `destination.bigquery.credentials` を検索します。

アクティブなパイプラインは、現在の DestinationCapabilitiesContext を他のコンポーネント（スキーマインスタンスなど）に提供します。
特に、命名規則や識別子の最大長を設定します。

一度にアクティブになるパイプラインは 1 つだけです。

`dlt.pipeline`/`dlt.attach` で作成またはアタッチされたパイプラインは自動的にアクティブになります。
`run`、`load`、`extract` メソッドもパイプラインをアクティブ化します。

## Container
複数のインジェクションコンテキストを保持するシングルトンインジェクションコンテナです。
基本的な辞書インターフェースを実装しています。

インジェクションコンテキストはその型によって識別され、辞書インデクサーを介して利用できます。
一般的なパターンとしては、コンテナ内にまだ存在しない場合は、デフォルトのコンテキスト値をインスタンス化します。

デフォルトでは、コンテキストはスレッド依存であるため、最初にコンテキストを設定したスレッドにのみインジェクトでき​​ます。
この動作は、特定のコンテキスト型（仕様）に応じて変更できます。

インデクサーは設定可能であり、値を明示的に設定できます。
これは、明示的にインスタンス化する必要があるすべてのコンテキストで必須です。

`injectable_context` を使用すると、`with` キーワードでコンテキストを設定し、スコープ外になった後に以前のコンテキストを復元できます。

## Pipeline.sync_destination
パイプラインの状態を、`dataset_name` に保存されている `destination` の状態と同期します。

### 注:
パイプラインの状態とスキーマを、出力先から復元しようとします。
出力先にある状態のバージョン番号は、作業ディレクトリにローカルに保存されている状態のバージョン番号よりも高い必要があります。
このような状況では、ローカルの状態、スキーマ、およびデータを含む中間ファイルは削除され、出力先にある状態とスキーマに置き換えられます。

パイプラインの状態がローカルに存在するものの、出力先にデータセットが存在しないという特殊なケースでは、ローカルの状態が消去されます。

注: このメソッドは、データに対する操作の前に `run` メソッドによって実行されます。
この動作を無効にするには、`restore_from_destination` 設定オプションを使用してください。

## Pipeline._sync_destination
### Pipeline._restore_state_from_destination
#### Pipeline._maybe_destination_capabilities
##### Pipeline._get_destination_capabilities
###### Destination.capabilities
出力先機能、つまりサポートされているローダーファイル形式、識別子名の長さ、命名規則、エスケープ関数など。
ファクトリー初期化関数に渡され、`caps_params` に格納された明示的な caps 引数が適用されます。

`config` が指定されている場合は、それが機能の調整に使用され、
指定されていない場合は、ファクトリー初期化関数に渡された `config_params` のみで構成される明示的な設定が適用されます。
`naming` が指定されている場合は、大文字と小文字の区別と大文字小文字の変換が調整されます。

#### Pipeline._get_destination_clients
##### get_destination_clients
出力先およびステージングジョブクライアントを作成し、それらを `schema` およびデータセット名にバインドします。
出力先 SPEC の設定は解決されます。

`multi_dataset_default_schema_name` が設定されている場合、`dataset_name` を取得するデフォルトスキーマを除き、
各 `schema` は `dataset_name__{schema.name}` という独自のデータセット名を取得します。

##### load_pipeline_state_from_destination
###### WithStateSync.get_stored_state
####### SqlJobClientBase.get_stored_state
### Pipeline._props_to_state
パイプラインのプロパティを `state` に書き込み、チェーンのためにそれを返します

### bump_pipeline_state_version_if_modified
#### bump_state_version_if_modified
コンテンツが変更された場合は、`state` バージョンとバージョン ハッシュをバンプし、
(新しいバージョン、新しいハッシュ、古いハッシュ) タプルを返します。

### Pipeline._save_state
#### FileStorage.save
##### FileStorage.save_atomic
f.write

## Pipeline.list_extracted_load_packages
Returns a list of all load packages ids that are or will be normalized.
### Pipeline._get_normalize_storage
#### Pipeline._normalize_storage_config
normalize_volume_path=os.path.join(self.working_dir, "normalize")

##### NormalizeStorageConfiguration
###### BaseConfiguration

## @configspec
任意のデコレートされたクラスを、設定を解決するための仕様として使用できる Python データクラスに変換します（派生クラス経由）。

`__init__` メソッドはデフォルトで合成されます。
デコレートされたクラスがカスタム `__init__` を実装している場合、および
いずれかの基底クラスに合成された `__init__` がない場合、`init` フラグは無視されます。

すべてのフィールドにはデフォルト値が必要です。
このデコレータは、デフォルト値が不足しているフィールドに `None` を追加します。

Python データクラスと比較すると、仕様は属性に対して完全な辞書インターフェースを実装し、
文字列やその他の型（解析、デシリアライズ）からのインスタンス作成と、設定解決プロセスの制御を可能にします。
詳細については、`BaseConfiguration` および `CredentialsConfiguration` を参照してください。

## Pipeline.list_normalized_load_packages
### Pipeline._get_load_storage
#### Pipeline._get_destination_capabilities
#### Pipeline._load_storage_config
##### LoadStorageConfiguration


## Pipeline.extract
`data` を抽出し、正規化の準備をします。
出力先や認証情報の設定は不要です。
引数の説明については、`run` メソッドを参照してください。

### Extract
#### Extract.__init__
##### ExtractStorage
###### ExtractStorage.__init__
####### PackageStorage
FileStorage(os.path.join(self.storage.storage_path, self.new_packages_folder)), "new"

####### ExtractorItemStorage
######## DataWriter.writer_spec_from_file_format
cls.class_factory(file_format, data_item_format, ALL_WRITERS).writer_spec()

### Pipeline._extract_source
#### Extract.extract
##### Extract._extract_single_source
###### Collector.update
カウンタを作成または更新します。

この関数は、カウンタ `name` を値 `inc` で更新します。
カウンタが存在しない場合は、オプションで合計値 `total` を指定してカウンタを作成します。
実装によっては、`label` を使用してネストされたカウンタを作成したり、
カウンタに関連付けられた追加情報を表示するための message を使用したりできます。

引数:
* name (str): 
    カウンタの一意の名前 (表示可能)。
* inc (int, オプション): 
    増加量。デフォルトは 1。
* total (int, オプション): 
    カウンタの最大値。デフォルトは None で、これはカウンタがバインドされていないことを意味します。
* icn_total (int, オプション): 
    カウンタの最大値を増加させます。カウンタがまだ終了していない場合は何も行いません。
* message (str, オプション): 
    カウンタに添付する追加メッセージ。デフォルトは None。
* label (str, オプション): 
    カウンタ `name` のネストされたカウンタを作成します。デフォルトは None です。

###### Extractor.write_items
`items` を `resource` に書き込み、オプションでテーブル スキーマを計算し、データの再検証/フィルタリングを行う

####### Extractor._write_to_static_table
####### Extractor._write_to_dynamic_table
######## Extractor._compute_and_update_tables
######## Extractor._import_item
######## Extractor._write_item
######### Collector.update


## Pipeline.normalize
`extract` メソッドで準備されたデータを正規化し、スキーマを推論して `load` メソッド用のロードパッケージを作成します。
`destination` を指定する必要があります。
### NormalizeConfiguration
### Normalize
### run_pool
#### Normalize.run
##### Collector.update
##### Normalize._step_info_start_load_id
##### Normalize.spool_schema_files
###### Normalize.spool_files
####### LoadStorage
####### PackageStorage.save_schema
####### PackageStorage.save_schema_updates
####### LoadStorage.commit_new_load_package

## Pipeline.load
`normalize` メソッドによって準備されたパッケージを `destination` の `dataset_name` にロードします。
オプションで、提供された `credentials` を使用します。

### Pipeline._get_destination_clients
### LoaderConfiguration
### Load
### run_pool
#### Load.run
##### Load._step_info_start_load_id
##### Load.load_single_package
###### Load.get_destination_client
###### LoadStorage.begin_schema_update
###### JobClientBase.should_truncate_table_before_load
###### JobClientBase.should_load_data_to_staging_dataset
###### LoadStorage.commit_schema_update
###### Load.resume_started_jobs
###### Load.complete_jobs
メインスレッドで定期的に実行され、ジョブ実行ステータスを収集します。

ステータスの変化を検出すると、ジョブの状態を適切なフォルダに移動してコミットします。
1つ以上のフォローアップジョブが新規ジョブとしてスケジュールされる場合があります。
新規ジョブは、終了状態（完了 / 失敗）の場合にのみ作成されます。

###### Load.start_new_jobs
new_jobs フォルダからジョブを取得し、利用可能なスロットの数だけジョブを開始します。

####### Load.