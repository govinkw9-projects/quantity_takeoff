export const Configuration = {
    audio_chunk_size : 10*1000, // Record in small chunks (e.g., every 250ms)
    transcript_ws : "ws://localhost:8000/ws/transcribe", //websocket connection to transcript audio
    transcript_api: "http://localhost:8000/api/transcribe", 
    fill_report_transcribe_api: "http://localhost:8000/api/fillpdf_transcribe",
    process_complete_plan_api: "http://0.0.0.0:8080/process_complete_plan?page_num=1", 
    S3_BUCKET_NAME:"dpasaps",
    localAudioLocation: '../DATA', 
     dpi: 200, // DPI used when converting PDF to image
    pdfJsScaleFactor : 7.0 // Scale factor used in PDF.js   
}