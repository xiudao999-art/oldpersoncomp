import streamlit as st
from bokeh.models import Div
from streamlit_bokeh_events import streamlit_bokeh_events
import base64
import uuid

def audio_recorder_ptt(
    text="",
    recording_color="#d93025",
    neutral_color="#07C160",
    icon_name="microphone",
    icon_size="2x",
    key="ptt_recorder_component_v5"
):
    """
    WeChat-style Hold-to-Talk audio recorder component.
    Supports both Mouse Click/Hold and Spacebar.
    Returns:
        bytes: Audio data in WAV format (16k 16bit mono).
    """
    
    # Use fixed IDs to avoid re-mounting issues, but allow multiple instances if needed
    btn_id = f"wechat-ptt-btn-{key}"
    status_id = f"wechat-ptt-status-{key}"
    
    # Updated JS code to capture RAW PCM and encode as WAV (16k 16bit mono)
    # Compact style for side-by-side layout (Icon Style)
    html_code = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0; padding: 0;">
        <button id="{btn_id}" style="
            width: 40px;
            height: 40px;
            background-color: {neutral_color};
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.1s;
            user-select: none;
            -webkit-user-select: none;
            display: flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
        ">🎤</button>
        <div id="{status_id}" style="display: none;">准备就绪</div>
    </div>
    
    <img src="x" style="display:none" onerror='
        (function() {{
            const btn = document.getElementById("{btn_id}");
            const status = document.getElementById("{status_id}");
            
            if (!btn) return;
            // Prevent re-attaching to the same button element
            if (btn.dataset.initialized) return;
            btn.dataset.initialized = "true";
            
            let audioContext;
            let mediaStreamSource;
            let scriptProcessor;
            let audioBuffers = [];
            let isRecording = false;
            let stream = null;
            
            // Helper function to encode WAV
            function encodeWAV(samples, sampleRate) {{
                const buffer = new ArrayBuffer(44 + samples.length * 2);
                const view = new DataView(buffer);
                
                const writeString = (view, offset, string) => {{
                    for (let i = 0; i < string.length; i++) {{
                        view.setUint8(offset + i, string.charCodeAt(i));
                    }}
                }};
                
                writeString(view, 0, "RIFF");
                view.setUint32(4, 36 + samples.length * 2, true);
                writeString(view, 8, "WAVE");
                writeString(view, 12, "fmt ");
                view.setUint32(16, 16, true);
                view.setUint16(20, 1, true);
                view.setUint16(22, 1, true);
                view.setUint32(24, sampleRate, true);
                view.setUint32(28, sampleRate * 2, true);
                view.setUint16(32, 2, true);
                view.setUint16(34, 16, true);
                writeString(view, 36, "data");
                view.setUint32(40, samples.length * 2, true);
                
                for (let i = 0; i < samples.length; i++) {{
                    view.setInt16(44 + i * 2, samples[i], true);
                }}
                
                return view;
            }}
            
            // Initial Setup
            // status.innerText = "⏳";
            
            navigator.mediaDevices.getUserMedia({{ audio: true }})
                .then(s => {{
                    stream = s;
                    // status.innerText = "✅";
                    
                    const start = () => {{
                        if (isRecording) return;
                        
                        isRecording = true;
                        audioBuffers = [];
                        
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        mediaStreamSource = audioContext.createMediaStreamSource(stream);
                        // Buffer size 4096, 1 input channel, 1 output channel
                        scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
                        
                        scriptProcessor.onaudioprocess = function(event) {{
                            if (!isRecording) return;
                            const input = event.inputBuffer.getChannelData(0);
                            // Clone data because input buffer is reused
                            audioBuffers.push(new Float32Array(input));
                        }};
                        
                        mediaStreamSource.connect(scriptProcessor);
                        scriptProcessor.connect(audioContext.destination);
                        
                        btn.innerText = "⏺️";
                        btn.style.backgroundColor = "{recording_color}";
                        btn.style.transform = "scale(0.95)";
                        // status.innerText = "🎤";
                    }};
                    
                    const stop = () => {{
                        if (!isRecording) return;
                        
                        isRecording = false;
                        
                        // Stop processing
                        if (mediaStreamSource) mediaStreamSource.disconnect();
                        if (scriptProcessor) scriptProcessor.disconnect();
                        if (audioContext) audioContext.close();
                        
                        btn.innerText = "🎤";
                        btn.style.backgroundColor = "{neutral_color}";
                        btn.style.transform = "scale(1)";
                        // status.innerText = "📤";
                        
                        // Process Audio
                        if (audioBuffers.length === 0) {{
                            // status.innerText = "❌";
                            return;
                        }}
                        
                        // Flatten
                        let totalLength = audioBuffers.reduce((acc, val) => acc + val.length, 0);
                        let rawData = new Float32Array(totalLength);
                        let offset = 0;
                        for (let i = 0; i < audioBuffers.length; i++) {{
                            rawData.set(audioBuffers[i], offset);
                            offset += audioBuffers[i].length;
                        }}
                        
                        // Downsample to 16000Hz
                        const targetRate = 16000;
                        const originalRate = audioContext ? audioContext.sampleRate : 44100; // Default or captured
                        const compression = originalRate / targetRate;
                        const length = Math.floor(rawData.length / compression);
                        const result = new Int16Array(length);
                        
                        for (let i = 0; i < length; i++) {{
                            let s = rawData[Math.floor(i * compression)];
                            // Clip and convert to Int16
                            result[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }}
                        
                        // Encode WAV
                        const view = encodeWAV(result, targetRate);
                        const blob = new Blob([view], {{ type: "audio/wav" }});
                        
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = () => {{
                            const base64data = reader.result;
                            document.dispatchEvent(new CustomEvent("GET_AUDIO", {{detail: {{audio_data: base64data}}}}));
                        }};
                        
                        // setTimeout(() => status.innerText = "✅", 1500);
                    }};
                    
                    // Mouse/Touch Events (Directly on button)
                    btn.onmousedown = (e) => {{ e.preventDefault(); start(); }};
                    btn.onmouseup = (e) => {{ e.preventDefault(); stop(); }};
                    btn.onmouseleave = (e) => {{ if(isRecording) stop(); }};
                    
                    btn.ontouchstart = (e) => {{ e.preventDefault(); start(); }};
                    btn.ontouchend = (e) => {{ e.preventDefault(); stop(); }};
                    
                    // Keyboard Events (Spacebar) - Global
                    const handleKeyDown = (e) => {{
                        if (e.code === "Space" && !isRecording) {{
                            e.preventDefault(); // Prevent scrolling
                            start();
                        }}
                    }};
                    
                    const handleKeyUp = (e) => {{
                        if (e.code === "Space" && isRecording) {{
                            e.preventDefault();
                            stop();
                        }}
                    }};
                    
                    // Cleanup old listeners if they exist
                    if (window.ptt_keydown) document.removeEventListener("keydown", window.ptt_keydown);
                    if (window.ptt_keyup) document.removeEventListener("keyup", window.ptt_keyup);
                    
                    // Register new
                    window.ptt_keydown = handleKeyDown;
                    window.ptt_keyup = handleKeyUp;
                    
                    document.addEventListener("keydown", handleKeyDown);
                    document.addEventListener("keyup", handleKeyUp);
                    
                }})
                .catch(err => {{
                    console.error(err);
                    // status.innerText = "❌";
                    btn.style.backgroundColor = "#ff4d4f";
                    btn.disabled = true;
                }});
        }})()
    '>
    """
    
    # Use Div to render HTML
    div = Div(text=html_code, width=50, height=50)
    
    result = streamlit_bokeh_events(
        bokeh_plot=div,
        events="GET_AUDIO",
        key=key,
        refresh_on_update=False,
        override_height=50,
        debounce_time=0
    )
    
    if result and "GET_AUDIO" in result:
        data = result.get("GET_AUDIO")
        if data and "audio_data" in data:
            b64_str = data["audio_data"]
            if "," in b64_str:
                header, encoded = b64_str.split(",", 1)
                return base64.b64decode(encoded)
            
    return None
