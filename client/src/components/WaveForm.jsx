import { useRef, useEffect } from 'react';

const Waveform = ({ audioLevel = 0 }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Set colors based on audio level
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, '#3b82f6');
    gradient.addColorStop(0.5, '#60a5fa');
    gradient.addColorStop(1, '#93c5fd');
    
    // Draw the baseline
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Draw the waveform
    const barWidth = 3;
    const barGap = 2;
    const barCount = Math.floor(width / (barWidth + barGap));
    const centerY = height / 2;
    
    for (let i = 0; i < barCount; i++) {
      const x = i * (barWidth + barGap);
      
      // Create a sine wave effect with random variations
      const angle = (i / barCount) * Math.PI * 6;
      const variance = Math.random() * 0.3;
      let magnitude = Math.sin(angle) * 0.3 + variance;
      
      // Scale by audio level with smoothing
      magnitude = magnitude * audioLevel * height * 0.4;
      
      // Draw the bar (extending from center)
      ctx.fillStyle = gradient;
      ctx.fillRect(x, centerY - magnitude, barWidth, magnitude * 2);
    }
    
    // Add a heartbeat effect if there's significant audio
    if (audioLevel > 0.3) {
      const heartbeatX = width - 40;
      const heartbeatY = 15;
      
      ctx.beginPath();
      ctx.moveTo(heartbeatX - 20, heartbeatY);
      ctx.lineTo(heartbeatX - 10, heartbeatY);
      ctx.lineTo(heartbeatX - 5, heartbeatY - 10);
      ctx.lineTo(heartbeatX, heartbeatY + 10);
      ctx.lineTo(heartbeatX + 5, heartbeatY - 5);
      ctx.lineTo(heartbeatX + 10, heartbeatY);
      ctx.lineTo(heartbeatX + 20, heartbeatY);
      
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    
  }, [audioLevel]);
  
  return (
    <div className="w-full rounded-lg overflow-hidden">
      <div className="bg-white p-1 rounded-lg">
        <canvas 
          ref={canvasRef} 
          width={500} 
          height={80} 
          className="w-full h-auto"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1 px-2">
          <span>0s</span>
          <span>Audio Level: {Math.round(audioLevel * 100)}%</span>
          <span>15s</span>
        </div>
      </div>
    </div>
  );
};

export default Waveform;