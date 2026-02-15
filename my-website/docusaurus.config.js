// @ts-check

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Physical AI & Humanoid Robotics',
  tagline: 'Explore the future of Physical AI and Humanoid Robotics',

  url: 'https://physical-ai-and-humanoid-robotics-gamma.vercel.app',
  baseUrl: '/',

  organizationName: 'hackathon',
  projectName: 'physical-ai-robotics',

  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'light',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'Physical AI & Robotics',
        hideOnScroll: true,
        items: [
          {
            to: '/docs/table-of-contents',
            position: 'left',
            label: 'Book',
          },
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Chapters',
          },
          {
            to: '/ChatPage',
            label: 'RAG Chat',
            position: 'left',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Learn',
            items: [
              {
                label: 'Table of Contents',
                to: '/docs/table-of-contents',
              },
              {
                label: 'Physical AI Curriculum',
                to: '/docs/chapter6-physical-ai',
              },
            ],
          },
          {
            title: 'Tools',
            items: [
              {
                label: 'RAG Chat Assistant',
                to: '/ChatPage',
              },
            ],
          },
          {
            title: 'Course',
            items: [
              {
                label: 'Home',
                to: '/',
              },
              {
                label: 'All Chapters',
                to: '/docs/table-of-contents',
              },
            ],
          },
        ],
        copyright: `Copyright ${new Date().getFullYear()} Physical AI & Humanoid Robotics. Built for the future.`,
      },
      prism: {
        theme: require('prism-react-renderer').themes.github,
        darkTheme: require('prism-react-renderer').themes.dracula,
      },
    }),
};

module.exports = config;
