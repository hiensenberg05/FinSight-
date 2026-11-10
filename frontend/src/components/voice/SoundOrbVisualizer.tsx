import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { VoiceState } from '../../types';
import { useReducedMotion } from 'framer-motion';

interface SoundOrbVisualizerProps {
  voiceState: VoiceState;
  audioLevel?: number;
  onToggle?: () => void;
  idleLabel?: string;
  className?: string;
}

export const SoundOrbVisualizer: React.FC<SoundOrbVisualizerProps> = ({
  voiceState,
  audioLevel = 0,
  onToggle,
  idleLabel = 'Tap to speak',
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const reduceMotion = useReducedMotion();

  // References for live animation loop
  const stateRef = useRef({
    voiceState,
    audioLevel,
    isHovered: false,
    mouse: { x: 0, y: 0 },
    targetRot: { x: 0, y: 0 },
    isDragging: false,
    dragStart: { x: 0, y: 0 },
    dragRot: { x: 0, y: 0 },
  });

  useEffect(() => {
    stateRef.current.voiceState = voiceState;
    stateRef.current.audioLevel = audioLevel;
    stateRef.current.isHovered = isHovered;
  }, [voiceState, audioLevel, isHovered]);

  const isListening = voiceState === 'listening';
  const isThinking = voiceState === 'thinking' || voiceState === 'processing' || voiceState === 'tool_execution';
  const isSpeaking = voiceState === 'speaking';
  const isError = voiceState === 'error';

  const getOrbLabel = () => {
    switch (voiceState) {
      case 'thinking':
      case 'processing':
        return 'Thinking...';
      case 'tool_execution':
        return 'Working...';
      case 'speaking':
        return 'Speaking...';
      case 'error':
        return 'Try again';
      case 'listening':
        return 'Listening...';
      case 'interrupted':
        return 'Interrupted';
      case 'idle':
      default:
        return idleLabel;
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const width = container.clientWidth || 250;
    const height = container.clientHeight || 250;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.z = 4.5;

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);

    // 2. Main 3D Root Group
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // Helper: Glow Dot Texture for Orbital Particle Rings
    const createDotTexture = () => {
      const texCanvas = document.createElement('canvas');
      texCanvas.width = 64;
      texCanvas.height = 64;
      const ctx = texCanvas.getContext('2d');
      if (ctx) {
        const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
        gradient.addColorStop(0.2, 'rgba(216, 180, 254, 0.95)');
        gradient.addColorStop(0.55, 'rgba(139, 92, 246, 0.35)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 64, 64);
      }
      return new THREE.CanvasTexture(texCanvas);
    };

    const dotTexture = createDotTexture();

    // 3. Concentric Orbital Dotted Particle Rings (from reference design)
    const particleRingsGroup = new THREE.Group();
    rootGroup.add(particleRingsGroup);

    const ringRadii = [1.68, 1.95, 2.22];
    const ringDotCounts = [64, 88, 112];
    const ringSystems: THREE.Points[] = [];

    ringRadii.forEach((radius, rIdx) => {
      const count = ringDotCounts[rIdx];
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2;
        positions[i * 3] = Math.cos(angle) * radius;
        positions[i * 3 + 1] = Math.sin(angle) * radius;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 0.05;
      }
      const ringGeo = new THREE.BufferGeometry();
      ringGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

      const ringMat = new THREE.PointsMaterial({
        size: 0.068,
        map: dotTexture,
        transparent: true,
        opacity: 0.48 - rIdx * 0.09,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      const points = new THREE.Points(ringGeo, ringMat);
      particleRingsGroup.add(points);
      ringSystems.push(points);
    });

    // 4. Multi-Layer Fluid 3D Silk Ribbons (Broad, flowing silk curves)
    const ribbonGroup = new THREE.Group();
    rootGroup.add(ribbonGroup);

    const ribbonVertexShader = `
      uniform float uTime;
      uniform float uRibbonIndex;
      uniform float uTotalRibbons;
      uniform float uAudioLevel;
      uniform float uSpeed;
      uniform float uRadius;
      uniform float uWidth;
      uniform float uAmplitude;

      varying vec2 vUv;
      varying float vWidthCoord;
      varying float vAngle;
      varying vec3 vNormalVec;

      void main() {
        vUv = uv;
        vWidthCoord = position.y * 2.0; // -1.0 to 1.0

        float angle = uv.x * 6.28318530718; // 0 to 2PI
        vAngle = angle;

        float phase = (uRibbonIndex / uTotalRibbons) * 6.28318530718;
        float t = uTime * uSpeed;

        // Broad, graceful sinusoidal wave harmonics (silk curves)
        float waveA = sin(angle * 2.0 + t * 1.1 + phase) * 0.16;
        float waveB = cos(angle * 3.0 - t * 0.85 + phase * 1.3) * 0.12;
        float waveC = sin(angle * 1.0 + t * 0.6) * 0.06;
        float audioTurbulence = uAudioLevel * 0.35 * sin(angle * 4.0 + t * 2.5);

        float currentRadius = uRadius + (waveA + waveB + waveC + audioTurbulence) * uAmplitude;

        // Smooth axial Z-depth undulation
        float zWave = sin(angle * 2.0 - t * 0.95 + phase) * 0.28
                    + cos(angle * 3.0 + t * 0.75 + phase * 1.5) * 0.16;

        vec3 centerPos = vec3(
          cos(angle) * currentRadius,
          sin(angle) * currentRadius,
          zWave * uAmplitude
        );

        // Approximate curve tangent
        float dAngle = 0.05;
        float nAngle = angle + dAngle;
        float nWaveA = sin(nAngle * 2.0 + t * 1.1 + phase) * 0.16;
        float nWaveB = cos(nAngle * 3.0 - t * 0.85 + phase * 1.3) * 0.12;
        float nWaveC = sin(nAngle * 1.0 + t * 0.6) * 0.06;
        float nZWave = sin(nAngle * 2.0 - t * 0.95 + phase) * 0.28
                     + cos(nAngle * 3.0 + t * 0.75 + phase * 1.5) * 0.16;

        vec3 nextPos = vec3(
          cos(nAngle) * (uRadius + (nWaveA + nWaveB + nWaveC) * uAmplitude),
          sin(nAngle) * (uRadius + (nWaveA + nWaveB + nWaveC) * uAmplitude),
          nZWave * uAmplitude
        );

        vec3 tangent = normalize(nextPos - centerPos);
        vec3 normalOut = normalize(vec3(centerPos.xy, 0.0));
        vec3 binormal = normalize(cross(tangent, normalOut));

        // Broad ribbon extrusion across width
        vec3 worldPos = centerPos + binormal * (position.y * uWidth);
        vNormalVec = normalize(cross(binormal, tangent));

        gl_Position = projectionMatrix * modelViewMatrix * vec4(worldPos, 1.0);
      }
    `;

    const ribbonFragmentShader = `
      uniform float uTime;
      uniform float uRibbonIndex;
      uniform float uAudioLevel;
      uniform float uOpacity;

      varying vec2 vUv;
      varying float vWidthCoord;
      varying float vAngle;
      varying vec3 vNormalVec;

      // Exact color spectrum from the voice logo reference
      const vec3 COLOR_CYAN    = vec3(0.04, 0.88, 1.00); // #0AE0FF (Bottom-left)
      const vec3 COLOR_AZURE   = vec3(0.18, 0.45, 1.00); // #2E73FF (Bottom)
      const vec3 COLOR_MAGENTA = vec3(1.00, 0.08, 0.65); // #FF14A6 (Right & Top-right)
      const vec3 COLOR_FUCHSIA = vec3(0.92, 0.25, 0.88); // #EB40E0 (Top-right)
      const vec3 COLOR_VIOLET  = vec3(0.60, 0.25, 0.98); // #9940FA (Top & Top-left)
      const vec3 COLOR_INDIGO  = vec3(0.35, 0.20, 0.90); // #5933E6 (Left)

      vec3 getSilkGradient(float angle) {
        float n = fract((angle + 1.57079632679) / 6.28318530718);

        if (n < 0.25) {
          return mix(COLOR_CYAN, COLOR_AZURE, smoothstep(0.0, 1.0, n / 0.25));
        } else if (n < 0.5) {
          return mix(COLOR_AZURE, COLOR_MAGENTA, smoothstep(0.0, 1.0, (n - 0.25) / 0.25));
        } else if (n < 0.75) {
          return mix(COLOR_MAGENTA, COLOR_VIOLET, smoothstep(0.0, 1.0, (n - 0.5) / 0.25));
        } else {
          return mix(COLOR_VIOLET, COLOR_CYAN, smoothstep(0.0, 1.0, (n - 0.75) / 0.25));
        }
      }

      void main() {
        vec3 baseColor = getSilkGradient(vAngle + uTime * 0.06);

        // Soft, luminous translucent silk sheet with crisp rim sheen
        float edgeDist = abs(vWidthCoord); // 0 at center, 1 at edge
        float rimSheen = pow(edgeDist, 3.5) * 2.4;
        float bodyFill = (1.0 - pow(edgeDist, 2.2)) * 0.5;

        // Normal lighting sheen
        float lightSheen = max(0.0, dot(vNormalVec, normalize(vec3(0.3, 0.5, 1.0)))) * 0.4;

        vec3 finalColor = baseColor * (0.85 + rimSheen * 1.5 + lightSheen);

        // Additive translucent silk blend
        float alpha = (bodyFill + rimSheen * 0.65) * uOpacity * (0.85 + uAudioLevel * 0.35);

        gl_FragColor = vec4(finalColor, alpha);
      }
    `;

    // 5 overlapping parametric 3D ribbons
    const ribbonCount = 5;
    const ribbonMeshes: THREE.Mesh[] = [];
    const ribbonMaterials: THREE.ShaderMaterial[] = [];

    const segmentsU = 160;
    const segmentsV = 16;
    const ribbonGeo = new THREE.PlaneGeometry(1, 1, segmentsU, segmentsV);

    for (let i = 0; i < ribbonCount; i++) {
      const mat = new THREE.ShaderMaterial({
        vertexShader: ribbonVertexShader,
        fragmentShader: ribbonFragmentShader,
        uniforms: {
          uTime: { value: 0 },
          uRibbonIndex: { value: i },
          uTotalRibbons: { value: ribbonCount },
          uAudioLevel: { value: 0 },
          uSpeed: { value: 1.0 },
          uRadius: { value: 1.25 },
          uWidth: { value: 0.65 },
          uAmplitude: { value: 1.0 },
          uOpacity: { value: 0.88 },
        },
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide,
      });

      const mesh = new THREE.Mesh(ribbonGeo, mat);
      ribbonGroup.add(mesh);
      ribbonMeshes.push(mesh);
      ribbonMaterials.push(mat);
    }

    // 5. Interactive Mouse & Drag Handling
    const handlePointerMove = (e: PointerEvent) => {
      const rect = container.getBoundingClientRect();
      const clientX = e.clientX;
      const clientY = e.clientY;

      if (
        clientX >= rect.left &&
        clientX <= rect.right &&
        clientY >= rect.top &&
        clientY <= rect.bottom
      ) {
        stateRef.current.isHovered = true;
        const normX = (clientX - rect.left) / rect.width - 0.5;
        const normY = (clientY - rect.top) / rect.height - 0.5;

        if (stateRef.current.isDragging) {
          const deltaX = clientX - stateRef.current.dragStart.x;
          const deltaY = clientY - stateRef.current.dragStart.y;
          stateRef.current.dragRot.y += deltaX * 0.01;
          stateRef.current.dragRot.x += deltaY * 0.01;
          stateRef.current.dragStart = { x: clientX, y: clientY };
        } else {
          // Interactive 3D tilt tracking (Parallax)
          stateRef.current.targetRot.x = normY * 0.65;
          stateRef.current.targetRot.y = normX * 0.65;
        }
      } else {
        stateRef.current.isHovered = false;
        stateRef.current.targetRot = { x: 0, y: 0 };
      }
    };

    const handlePointerDown = (e: PointerEvent) => {
      stateRef.current.isDragging = true;
      stateRef.current.dragStart = { x: e.clientX, y: e.clientY };
    };

    const handlePointerUp = () => {
      stateRef.current.isDragging = false;
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    window.addEventListener('pointerup', handlePointerUp);
    container.addEventListener('pointerdown', handlePointerDown);

    // 6. Animation Loop (60 FPS)
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      if (reduceMotion) {
        renderer.render(scene, camera);
        return;
      }
      animationFrameId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();
      const currentVoiceState = stateRef.current.voiceState;
      const currentAudio = stateRef.current.audioLevel;

      // Dynamics based on voiceState
      let speedMult = 1.0;
      let amplitudeMult = 1.0;
      let opacityVal = 0.88;

      if (currentVoiceState === 'listening') {
        speedMult = 1.3 + currentAudio * 1.4;
        amplitudeMult = 1.1 + currentAudio * 0.45;
        opacityVal = 0.95;
      } else if (currentVoiceState === 'thinking') {
        speedMult = 2.2;
        amplitudeMult = 0.95;
        opacityVal = 0.92;
      } else if (currentVoiceState === 'speaking') {
        speedMult = 1.25;
        amplitudeMult = 1.12;
        opacityVal = 0.92;
      } else if (currentVoiceState === 'error') {
        speedMult = 0.6;
        amplitudeMult = 0.8;
        opacityVal = 0.7;
      }

      // Update Ribbon Uniforms
      ribbonMaterials.forEach((mat) => {
        mat.uniforms.uTime.value = elapsedTime;
        mat.uniforms.uAudioLevel.value = currentAudio;
        mat.uniforms.uSpeed.value = speedMult;
        mat.uniforms.uAmplitude.value = amplitudeMult;
        mat.uniforms.uOpacity.value = opacityVal;
      });

      // Continuous 3D rotation of ribbons around Z-axis
      ribbonGroup.rotation.z += 0.006 * speedMult;

      // Rotate particle rings in 3D
      ringSystems.forEach((ring, idx) => {
        ring.rotation.z += 0.0025 * (idx % 2 === 0 ? 1 : -1);
      });

      // Smooth damped 3D tilt tracking (Parallax)
      const targetX = stateRef.current.targetRot.x + stateRef.current.dragRot.x;
      const targetY = stateRef.current.targetRot.y + stateRef.current.dragRot.y;

      rootGroup.rotation.x = THREE.MathUtils.lerp(rootGroup.rotation.x, targetX, 0.08);
      rootGroup.rotation.y = THREE.MathUtils.lerp(rootGroup.rotation.y, targetY, 0.08);

      // Audio-reactive scale
      const dynamicScale = currentVoiceState === 'listening'
        ? 1.0 + Math.min(currentAudio * 0.25, 0.2)
        : currentVoiceState === 'speaking'
        ? 1.02 + Math.sin(elapsedTime * 3.5) * 0.02
        : 1.0;

      rootGroup.scale.set(dynamicScale, dynamicScale, dynamicScale);

      renderer.render(scene, camera);
    };

    animate();

    // 7. Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      container.removeEventListener('pointerdown', handlePointerDown);

      dotTexture.dispose();
      ribbonGeo.dispose();
      ribbonMaterials.forEach((m) => m.dispose());
      ringSystems.forEach((r) => {
        r.geometry.dispose();
        (r.material as THREE.Material).dispose();
      });
      renderer.dispose();
    };
  }, [reduceMotion]);

  return (
    <div
      ref={containerRef}
      onClick={onToggle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="button"
      tabIndex={0}
      aria-label={`Interactive 3D Voice Assistant Orb - ${getOrbLabel()}`}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onToggle?.()}
      className={`relative w-[240px] h-[240px] sm:w-[250px] sm:h-[250px] flex items-center justify-center select-none cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 rounded-full flex-shrink-0 ${className}`}
    >
      {/* 1. Underlying Luminous Halo Ambient Glow */}
      <div 
        className="absolute inset-2 rounded-full opacity-65 filter blur-[30px] pointer-events-none transition-opacity duration-300 group-hover:opacity-85"
        style={{
          background: 'radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.35) 0%, rgba(6, 182, 212, 0.25) 45%, rgba(236, 72, 153, 0.25) 70%, transparent 100%)',
        }}
      />

      {/* 2. WebGL 3D Canvas (Live Rotating Interactive Silk Ribbons) */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none z-0 filter drop-shadow-[0_0_24px_rgba(139,92,246,0.35)]"
      />

      {/* 3. Central Dark Hub (diameter 96px - Exact match to Voice Logo) */}
      <div className="relative w-[96px] h-[96px] rounded-full bg-[#0D0B23] border border-violet-400/35 shadow-[0_0_36px_rgba(10,8,24,0.95),inset_0_0_16px_rgba(109,79,255,0.3)] flex flex-col items-center justify-center z-10 transition-transform duration-200 group-hover:scale-105 pointer-events-none">
        {/* 5-Bar Center Soundwave Glyph */}
        <div className="flex items-center gap-[3px] h-5 mb-1.5">
          <span 
            className={`w-[2px] rounded-full transition-all duration-100 ${
              isListening ? 'h-3 bg-cyan-300' : isSpeaking ? 'h-2.5 bg-violet-300' : 'h-2 bg-white/75'
            }`} 
          />
          <span 
            className={`w-[2px] rounded-full transition-all duration-100 ${
              isListening ? 'h-4 bg-white' : isSpeaking ? 'h-3.5 bg-white' : 'h-3 bg-white'
            }`} 
          />
          <span 
            className={`w-[2.5px] rounded-full transition-all duration-100 ${
              isListening ? 'h-5 bg-white' : isSpeaking ? 'h-5 bg-white' : 'h-4.5 bg-white'
            }`} 
          />
          <span 
            className={`w-[2px] rounded-full transition-all duration-100 ${
              isListening ? 'h-3.5 bg-white' : isSpeaking ? 'h-3.5 bg-white' : 'h-3 bg-white'
            }`} 
          />
          <span 
            className={`w-[2px] rounded-full transition-all duration-100 ${
              isListening ? 'h-2.5 bg-pink-300' : isSpeaking ? 'h-2 bg-violet-300' : 'h-1.5 bg-white/75'
            }`} 
          />
        </div>

        {/* Status Text: "Listening..." */}
        <span className="text-[12px] font-medium text-white tracking-tight leading-none text-center px-1">
          {getOrbLabel()}
        </span>
      </div>
    </div>
  );
};
