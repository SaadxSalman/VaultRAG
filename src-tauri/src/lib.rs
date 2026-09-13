#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[tauri::command]
fn app_name() -> &'static str {
    "VaultRAG"
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![app_name])
        .run(tauri::generate_context!())
        .expect("error while running VaultRAG");
}
