/**
 * BGCGW Student Attendance & Mark Register
 * 3D Icosahedron - Lilac geometric object with particles, edges, and smooth mouse interaction
 */

(function() {
    'use strict';

    const container = document.getElementById('canvas-3d');
    if (!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

    renderer.setSize(container.offsetWidth, container.offsetHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Icosahedron - solid lilac with wireframe edges
    const geometry = new THREE.IcosahedronGeometry(1.2, 1);
    const material = new THREE.MeshPhongMaterial({
        color: 0xe39df9,
        emissive: 0xf5d7ff,
        emissiveIntensity: 0.2,
        shininess: 50,
        specular: 0xf5d7ff
    });
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Wireframe overlay for highlighted edges
    const edgesGeometry = new THREE.EdgesGeometry(geometry);
    const edgesMaterial = new THREE.LineBasicMaterial({
        color: 0xe8b8f5,
        linewidth: 1
    });
    const wireframe = new THREE.LineSegments(edgesGeometry, edgesMaterial);
    mesh.add(wireframe);

    // Glowing spot (point light on front face)
    const glowLight = new THREE.PointLight(0xffddbb, 0.8, 3);
    glowLight.position.set(0.6, 0.6, 0.8);
    mesh.add(glowLight);

    // Soft orange/yellow background particles
    const particleCount = 80;
    const particlesGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 12;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 12;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 8 - 2;
        sizes[i] = Math.random() * 2 + 0.5;
    }
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particlesGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const particleMaterial = new THREE.PointsMaterial({
        color: 0xffcc88,
        size: 0.08,
        transparent: true,
        opacity: 0.6,
        sizeAttenuation: true
    });
    const particles = new THREE.Points(particlesGeometry, particleMaterial);
    scene.add(particles);

    // Golden star sparkles (#ecd540) orbiting around the 3D shape
    const starColor = 0xecd540;
    const starCount = 85;
    const starOrbitRadius = 2.2;
    const starAngles = [];
    const starHeights = [];
    const starSpeeds = [];

    for (let i = 0; i < starCount; i++) {
        starAngles.push(Math.random() * Math.PI * 2);
        starHeights.push((Math.random() - 0.5) * 2.5);
        starSpeeds.push(0.006 + Math.random() * 0.012);
    }

    const starsGeometry = new THREE.BufferGeometry();
    const starsPositions = new Float32Array(starCount * 3);

    function updateStarsPosition() {
        for (let i = 0; i < starCount; i++) {
            starAngles[i] += starSpeeds[i];
            starsPositions[i * 3] = Math.cos(starAngles[i]) * starOrbitRadius;
            starsPositions[i * 3 + 1] = starHeights[i];
            starsPositions[i * 3 + 2] = Math.sin(starAngles[i]) * starOrbitRadius;
        }
        starsGeometry.setAttribute('position', new THREE.BufferAttribute(starsPositions, 3));
        starsGeometry.attributes.position.needsUpdate = true;
    }
    updateStarsPosition();

    // Create starburst texture - luminous star with rays (#ecd540)
    function createStarTexture() {
        const size = 128;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        const cx = size / 2;
        const cy = size / 2;

        // Gold color #ecd540
        const gold = '#ecd540';
        const goldBright = '#f5e366';
        const goldFade = 'rgba(236, 213, 64, 0.3)';

        // Central bright glow
        const centerGradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 12);
        centerGradient.addColorStop(0, goldBright);
        centerGradient.addColorStop(0.4, gold);
        centerGradient.addColorStop(0.7, goldFade);
        centerGradient.addColorStop(1, 'rgba(236, 213, 64, 0)');
        ctx.fillStyle = centerGradient;
        ctx.beginPath();
        ctx.arc(cx, cy, 14, 0, Math.PI * 2);
        ctx.fill();

        // Draw rays - 4 primary (cross), 4 secondary (diagonal), 8 tertiary
        ctx.strokeStyle = gold;
        ctx.lineCap = 'round';

        for (let i = 0; i < 16; i++) {
            const angle = (i / 16) * Math.PI * 2;
            const isPrimary = i % 4 === 0;
            const isSecondary = i % 4 === 2;
            const length = isPrimary ? 60 : (isSecondary ? 45 : 28);
            const width = isPrimary ? 3 : (isSecondary ? 2 : 1);

            const gradient = ctx.createLinearGradient(cx, cy, cx + Math.cos(angle) * length, cy + Math.sin(angle) * length);
            gradient.addColorStop(0, goldBright);
            gradient.addColorStop(0.3, gold);
            gradient.addColorStop(0.8, goldFade);
            gradient.addColorStop(1, 'rgba(236, 213, 64, 0)');

            ctx.strokeStyle = gradient;
            ctx.lineWidth = width;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + Math.cos(angle) * length, cy + Math.sin(angle) * length);
            ctx.stroke();
        }

        const texture = new THREE.CanvasTexture(canvas);
        texture.needsUpdate = true;
        return texture;
    }

    const starTexture = createStarTexture();

    const starsMaterial = new THREE.PointsMaterial({
        color: starColor,
        size: 0.26,
        map: starTexture,
        transparent: true,
        opacity: 0.95,
        sizeAttenuation: true,
        alphaTest: 0.1,
        depthWrite: false
    });
    const stars = new THREE.Points(starsGeometry, starsMaterial);
    scene.add(stars);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    const fillLight = new THREE.DirectionalLight(0xf5d7ff, 0.35);
    fillLight.position.set(-5, -3, 2);
    scene.add(fillLight);

    camera.position.z = 4;

    // Faster, smoother mouse interaction
    let mouseX = 0;
    let mouseY = 0;
    let currentMouseX = 0;
    let currentMouseY = 0;
    const smoothFactor = 0.15;  // Higher = faster response
    const hoverMultiplier = 0.08;  // Stronger mouse influence

    container.addEventListener('mousemove', function(e) {
        const rect = container.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
        mouseY = -((e.clientY - rect.top) / rect.height - 0.5) * 2;
    });

    container.addEventListener('mouseleave', function() {
        mouseX = 0;
        mouseY = 0;
    });

    function animate() {
        requestAnimationFrame(animate);

        currentMouseX += (mouseX - currentMouseX) * smoothFactor;
        currentMouseY += (mouseY - currentMouseY) * smoothFactor;

        // Base rotation + faster hover response
        mesh.rotation.y += 0.005 + currentMouseX * hoverMultiplier;
        mesh.rotation.x += 0.002 + currentMouseY * hoverMultiplier;

        // Orbit star sparkles around the icosahedron
        updateStarsPosition();

        // Gentle particle drift
        const pos = particles.geometry.attributes.position.array;
        for (let i = 0; i < particleCount; i++) {
            pos[i * 3 + 1] += 0.002;
            if (pos[i * 3 + 1] > 6) pos[i * 3 + 1] = -6;
        }
        particles.geometry.attributes.position.needsUpdate = true;

        renderer.render(scene, camera);
    }

    function onResize() {
        const width = container.offsetWidth;
        const height = container.offsetHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    }

    window.addEventListener('resize', onResize);
    onResize();
    animate();
})();
