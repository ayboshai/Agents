export interface CompanyContacts {
  companyName: 'AB-Company';
  phone: '+79659903160';
  email: 'ticketbad@gmail.com';
  telegram: '@Ticket_lucky';
  whatsappUrl: string;
}

export interface HeroStat {
  title: string;
  description: string;
}

export interface ServiceItem {
  id: 'implementation' | 'adaptation' | 'rent' | 'marketplaces';
  title: string;
  description: string;
  icon: string;
}

export interface MarketplaceMetrics {
  grossProfitMultiplier: 'x3.9';
  revenueMultiplier: 'x4.2';
  turnoverMultiplier: 'x4.5';
}

export interface CaseStudy {
  slug: string;
  title: string;
  location: string;
  problem: string;
  solution: string;
  result: string;
}

export const companyData: CompanyContacts = {
  companyName: 'AB-Company',
  phone: '+79659903160',
  email: 'ticketbad@gmail.com',
  telegram: '@Ticket_lucky',
  whatsappUrl: 'https://wa.me/79659903160',
};

export const heroData: {
  headline: string;
  subhead: string;
  stats: HeroStat[];
} = {
  headline: 'Автоматизируем ваш бизнес на базе 1С и современных интеграций',
  subhead:
    'Внедряем, адаптируем и сопровождаем решения для роста прибыли, контроля процессов и быстрой масштабируемости.',
  stats: [
    {
      title: '10+ лет опыта',
      description: 'Реализуем проекты автоматизации в ритейле и B2B',
    },
    {
      title: '95% проектов в срок',
      description: 'Прозрачный план внедрения и контроль этапов',
    },
    {
      title: '24/7 поддержка',
      description: 'Оперативно реагируем на инциденты и запросы команд',
    },
    {
      title: 'ROI от 3 месяцев',
      description: 'Фокус на бизнес-результате и измеримых метриках',
    },
  ],
};

export const servicesData: ServiceItem[] = [
  {
    id: 'implementation',
    title: 'Внедрение 1С',
    description:
      'Полный цикл внедрения: от обследования до запуска и обучения команды.',
    icon: 'Rocket',
  },
  {
    id: 'adaptation',
    title: 'Адаптация решений',
    description:
      'Дорабатываем процессы под специфику вашей компании и отраслевые требования.',
    icon: 'Settings',
  },
  {
    id: 'rent',
    title: 'Аренда 1С',
    description:
      'Облачные конфигурации с безопасным доступом и техническим администрированием.',
    icon: 'Cloud',
  },
  {
    id: 'marketplaces',
    title: 'Интеграции с маркетплейсами',
    description:
      'Синхронизируем остатки, заказы и аналитику между 1С и площадками продаж.',
    icon: 'Store',
  },
];

export const marketplaceData: {
  title: string;
  description: string;
  benefits: string[];
  metrics: MarketplaceMetrics;
} = {
  title: 'Модуль маркетплейсов: продажи под полным контролем',
  description:
    'Единый контур управления каталогом, остатками и заказами для Ozon, Wildberries и других каналов.',
  benefits: [
    'Автоматическое обновление цен и остатков',
    'Снижение ручных операций и ошибок',
    'Сквозная аналитика по каналам продаж',
  ],
  metrics: {
    grossProfitMultiplier: 'x3.9',
    revenueMultiplier: 'x4.2',
    turnoverMultiplier: 'x4.5',
  },
};

export const casesData: CaseStudy[] = [
  {
    slug: 'retail-automation-kazan',
    title: 'Автоматизация сети розницы',
    location: 'Казань',
    problem: 'Ручной учет и задержки в обработке заказов.',
    solution: 'Внедрили 1С + интеграцию с CRM и складской логикой.',
    result: 'Сократили операционные затраты на 28% за 6 месяцев.',
  },
  {
    slug: 'b2b-distributor-moscow',
    title: 'Цифровой контур для B2B-дистрибьютора',
    location: 'Москва',
    problem: 'Разрозненные данные по продажам и закупкам.',
    solution: 'Объединили ERP, BI-отчетность и EDI-обмен.',
    result: 'Ускорили цикл обработки заказов в 2.1 раза.',
  },
  {
    slug: 'marketplace-scale-ekb',
    title: 'Рост продаж на маркетплейсах',
    location: 'Екатеринбург',
    problem: 'Ошибки остатков и штрафы за несвоевременные отгрузки.',
    solution: 'Подключили модуль синхронизации остатков и SLA-мониторинг.',
    result: 'Увеличили оборот в 4.5 раза за 9 месяцев.',
  },
];

export const leadFormContent = {
  title: 'Обсудим ваш проект',
  fields: {
    nameLabel: 'Имя',
    phoneLabel: 'Телефон',
    messageLabel: 'Сообщение',
  },
  submitButton: 'Оставить заявку',
  successMessage: 'Заявка успешно отправлена. Мы свяжемся с вами в ближайшее время.',
  genericErrorMessage: 'Не удалось отправить заявку. Попробуйте еще раз.',
} as const;

export const casesPreviewContent = {
  title: 'Кейсы клиентов',
  readMoreLabel: 'Read more',
} as const;
