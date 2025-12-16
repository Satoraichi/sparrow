//ブラウザのシステム設定 (prefers-color-scheme) に合わせた初期設定
function checkSystemPreference() {
  // システムがダークモードを優先しているか確認
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  // ローカルストレージに設定がなければ、システム設定に従う
  if (localStorage.getItem('theme') === null) {
    if (prefersDark) {
      document.body.classList.add('dark-mode');
    }
  }
}

//ページロード時にローカルストレージの設定を読み込む
function loadTheme() {
  const savedTheme = localStorage.getItem('theme');

  if (savedTheme === 'dark') {
    // 保存された設定が 'dark' なら、ダークモードを適用
    document.body.classList.add('dark-mode');
  } else if (savedTheme === 'light') {
    // 保存された設定が 'light' なら、ライトモードを適用（念のためクラスを削除）
    document.body.classList.remove('dark-mode');
  } else {
    // 設定が保存されていない場合はシステム設定をチェック
    checkSystemPreference(); 
  }
}

//ダークモードの切り替え関数 (HTMLのボタンから呼び出す)
function toggleDarkMode() {
  const body = document.body;
  
  // body要素に 'dark-mode' クラスがあるかチェック
  if (body.classList.contains('dark-mode')) {
    // ダークモードを解除
    body.classList.remove('dark-mode');
    localStorage.setItem('theme', 'light'); // 設定を 'light' で保存
  } else {
    // ダークモードを適用
    body.classList.add('dark-mode');
    localStorage.setItem('theme', 'dark'); // 設定を 'dark' で保存
  }
}

loadTheme();