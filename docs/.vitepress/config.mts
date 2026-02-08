import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "StepZero Docs",
  description: "Documentation for StepZero Project",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Plan', link: '/StepZero_Service_Plan' }
    ],

    sidebar: [
      {
        text: 'Planning',
        items: [
          { text: 'Service Plan', link: '/StepZero_Service_Plan' },
          { text: 'Chat Ideas', link: '/채팅' },
          { text: 'Feedback', link: '/피드백' }
        ]
      },
      {
        text: 'Brainstorming',
        items: [
          { text: 'Feedback Integration', link: '/brainstorm/Brainstorm- 피드백 항목 중 StepZero 기획안에 추가' },
          { text: 'Chat Interface Idea', link: '/brainstorm/Brainstorm- "채팅 입력" 인터페이스 아이디어' },
          { text: 'Business Model', link: '/brainstorm/Brainstorm- StepZero 비즈니스 모델(BM) 전략' },
          { text: 'Founder PT Concept', link: '/brainstorm/Brainstorm- "창업 PT 코치" 컨셉의 서비스 통합 전략' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/lastdays03/step-zero' }
    ]
  }
})
