import { Component, ElementRef, Input, OnChanges, SimpleChanges, ViewChild } from '@angular/core';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

@Component({
  selector: 'app-stl-viewer',
  template: `<div #canvasContainer class="stl-container"></div>`,
  styles: [`
    .stl-container {
      width: 100%;
      height: 400px;
      border-radius: 8px;
      overflow: hidden;
      background: #1e1e2f;
    }
  `]
})
export class StlViewerComponent implements OnChanges {
  @ViewChild('canvasContainer', { static: true }) canvasContainer!: ElementRef<HTMLDivElement>;
  @Input() stlUrl!: string; // URL du fichier STL hébergé sur Django REST

  private scene!: THREE.Scene;
  private camera!: THREE.PerspectiveCamera;
  private renderer!: THREE.WebGLRenderer;
  private controls!: OrbitControls;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['stlUrl'] && this.stlUrl) {
      this.initThreeJS();
      this.loadSTL(this.stlUrl);
    }
  }

  private initThreeJS(): void {
    const container = this.canvasContainer.nativeElement;
    container.innerHTML = '';

    // Scène & Caméra
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x23272a);

    this.camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    this.camera.position.set(0, 0, 100);

    // Éclairage
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(1, 1, 1).normalize();
    this.scene.add(dirLight);

    // Rendu WebGL
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(this.renderer.domElement);

    // Contrôler la vue (Rotation, Zoom avec la souris)
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;

    this.animate();
  }

  private loadSTL(url: string): void {
    const loader = new STLLoader();
    loader.load(url, (geometry) => {
      // Matériau d'aspect "Impression 3D" (ex: plastique orange)
      const material = new THREE.MeshPhongMaterial({ color: 0xff6b00, specular: 0x111111, shininess: 200 });
      const mesh = new THREE.Mesh(geometry, material);

      // Centrer automatiquement le modèle 3D sur la scène
      geometry.center();

      this.scene.add(mesh);
      this.renderer.render(this.scene, this.camera);
    });
  }

  private animate = (): void => {
    requestAnimationFrame(this.animate);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };
}