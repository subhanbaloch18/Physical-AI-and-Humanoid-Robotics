import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

const features = [
  {
    icon: '\uD83E\uDDE0',
    title: 'Embodied Intelligence',
    description:
      'Learn how AI agents perceive, reason, and act in the physical world through sensors, actuators, and neural architectures.',
  },
  {
    icon: '\u2699\uFE0F',
    title: 'ROS 2 & Robotics Middleware',
    description:
      'Master the Robot Operating System 2 (ROS 2) — the nervous system that connects sensors, actuators, and AI decision-making.',
  },
  {
    icon: '\uD83C\uDF10',
    title: 'Digital Twins & Simulation',
    description:
      'Build high-fidelity virtual replicas of robots using Gazebo and Unity to test behaviors before deploying to real hardware.',
  },
  {
    icon: '\uD83D\uDC41\uFE0F',
    title: 'Vision-Language-Action (VLA)',
    description:
      'Explore cutting-edge VLA models that unify vision, language understanding, and robotic action in a single architecture.',
  },
  {
    icon: '\uD83D\uDD04',
    title: 'Sim-to-Real Learning',
    description:
      'Train robots in simulation using NVIDIA Isaac and transfer learned policies to physical hardware with domain adaptation.',
  },
  {
    icon: '\uD83E\uDD16',
    title: 'Capstone: Autonomous Humanoid',
    description:
      'Design, build, and train a complete physical AI agent — from simulation to real-world deployment — in a team-based capstone.',
  },
];

const modules = [
  {
    number: '01',
    title: 'The Robotic Nervous System',
    subtitle: 'ROS 2',
    topics: ['ROS 2 Architecture', 'Nodes, Topics, Services', 'Creating ROS 2 Packages', 'Actions & Communication'],
  },
  {
    number: '02',
    title: 'The Digital Twin',
    subtitle: 'Gazebo & Unity',
    topics: ['Introduction to Simulation', 'Building Digital Twins', 'Gazebo-ROS 2 Integration', 'Advanced Unity Simulation'],
  },
  {
    number: '03',
    title: 'The AI-Robot Brain',
    subtitle: 'NVIDIA Isaac',
    topics: ['Isaac Sim & Isaac Gym', 'Training Robots in Simulation', 'Reinforcement Learning', 'Sim-to-Real Transfer'],
  },
  {
    number: '04',
    title: 'Vision-Language-Action',
    subtitle: 'VLA Models',
    topics: ['Introduction to VLAs', 'Building VLA Models', 'Training & Fine-tuning', 'Robot Deployment'],
  },
];

const techStack = [
  { name: 'ROS 2', category: 'Middleware' },
  { name: 'Gazebo', category: 'Simulation' },
  { name: 'Unity', category: 'Simulation' },
  { name: 'NVIDIA Isaac Sim', category: 'AI Training' },
  { name: 'NVIDIA Isaac ROS', category: 'Deployment' },
  { name: 'Jetson Orin', category: 'Edge AI' },
  { name: 'GPT / LLMs', category: 'Language AI' },
  { name: 'Cohere', category: 'Embeddings' },
];

const stats = [
  { number: '6', label: 'Chapters' },
  { number: '4', label: 'Core Modules' },
  { number: '13', label: 'Weeks' },
  { number: '1', label: 'Capstone Project' },
];

export default function Home() {
  return (
    <Layout title="Home" description="Physical AI & Humanoid Robotics - Bridging the Digital Brain and the Physical Body">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-bg-decoration">
          <div className="hero-orb hero-orb-1" />
          <div className="hero-orb hero-orb-2" />
          <div className="hero-orb hero-orb-3" />
        </div>

        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            Physical AI & Humanoid Robotics
          </div>

          <h1 className="hero-title">
            Bridging the{' '}
            <span className="hero-title-gradient">Digital Brain</span>
            {' '}and the{' '}
            <span className="hero-title-gradient">Physical Body</span>
          </h1>

          <p className="hero-subtitle">
            A comprehensive course on Physical AI and Humanoid Robotics — from ROS 2
            and simulation to Vision-Language-Action models and real-world deployment.
          </p>

          <div className="hero-actions">
            <Link to="/docs/table-of-contents" className="hero-btn-primary">
              <span className="hero-btn-icon">\uD83D\uDCDA</span>
              Start Learning
            </Link>
            <Link to="/docs/chapter6-physical-ai" className="hero-btn-secondary">
              <span className="hero-btn-icon">\uD83D\uDCC4</span>
              View Curriculum
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header">
          <span className="section-label">What You'll Learn</span>
          <h2 className="section-title">Core Topics & Skills</h2>
          <p className="section-description">
            From embodied intelligence to autonomous humanoid deployment — master
            the full stack of Physical AI and Robotics.
          </p>
        </div>

        <div className="features-grid">
          {features.map((feature, idx) => (
            <div className="feature-card" key={idx}>
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-card-title">{feature.title}</h3>
              <p className="feature-card-desc">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Course Modules Section */}
      <section className="modules-section">
        <div className="section-header">
          <span className="section-label">Course Structure</span>
          <h2 className="section-title">Four Core Modules</h2>
          <p className="section-description">
            A structured learning path that takes you from foundational robotics
            middleware to cutting-edge AI-powered autonomy.
          </p>
        </div>

        <div className="modules-grid">
          {modules.map((mod, idx) => (
            <div className="module-card" key={idx}>
              <div className="module-number">{mod.number}</div>
              <h3 className="module-card-title">{mod.title}</h3>
              <span className="module-card-subtitle">{mod.subtitle}</span>
              <ul className="module-topics">
                {mod.topics.map((topic, tidx) => (
                  <li key={tidx}>{topic}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-grid">
          {stats.map((stat, idx) => (
            <div className="stat-item" key={idx}>
              <div className="stat-number">{stat.number}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Technology Stack Section */}
      <section className="tech-section">
        <div className="section-header">
          <span className="section-label">Technology Stack</span>
          <h2 className="section-title">Tools & Platforms</h2>
          <p className="section-description">
            Industry-standard tools and frameworks used throughout the course.
          </p>
        </div>

        <div className="tech-grid">
          {techStack.map((tech, idx) => (
            <div className="tech-card" key={idx}>
              <div className="tech-card-name">{tech.name}</div>
              <div className="tech-card-category">{tech.category}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-card">
          <h2 className="cta-title">
            Ready to Build the Future?
          </h2>
          <p className="cta-desc">
            Explore the course material or ask questions about Physical AI and
            Humanoid Robotics using our RAG-powered assistant.
          </p>
          <div className="hero-actions">
            <Link to="/ChatPage" className="hero-btn-primary">
              <span className="hero-btn-icon">\uD83D\uDCAC</span>
              Ask AI Assistant
            </Link>
            <Link to="/docs/table-of-contents" className="hero-btn-secondary">
              <span className="hero-btn-icon">\uD83D\uDCDA</span>
              Browse Chapters
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}
