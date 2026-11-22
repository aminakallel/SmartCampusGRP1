export interface Translation {
  common: {
    home: string;
    talkToAssistant: string;
    continue: string;
    back: string;
    retry: string;
    soon: string;
    example: string;
    demoData: string;
  };
  nav: {
    skipToContent: string;
    openMenu: string;
    closeMenu: string;
    theme: string;
    themeLight: string;
    themeDark: string;
    /** Texte du bouton de préinscription (lien externe). */
    preinscriptionCta: string;
    /** Précision pour les lecteurs d'écran (lien externe). */
    opensOnFacultySite: string;
  };
  footer: {
    description: string;
    institutions: string;
    iitFull: string;
    isbFull: string;
    team: string;
    admissions: string;
    copyright: string;
  };
  home: {
    heroTitle: string;
    heroSubtitle: string;
    assurances: string[];
    ctaHint: string;
  };
  chat: {
    title: string;
    online: string;
    isTyping: string;
    placeholder: string;
    sendMessage: string;
    enterHint: string;
    demoMode: string;
    error: string;
    welcome: string;
    suggestions: string[];
    open: string;
    close: string;
    minimize: string;
    expand: string;
    voiceSoon: string;
    messageLabel: string;
    retry: string;
    /** Libellé du bouton flottant quand le chat est réduit. */
    discuss: string;
    /** Libellé du point de notification. */
    notification: string;
    introFormations: string;
    introAdmission: string;
    introProspects: string;
    introGeneral: string;
    noMatch: string;
    showMore: string;
    cardConditions: string;
    cardProspects: string;
    levelLabel: string;
    durationLabel: string;
  };
  dashboard: {
    title: string;
    subtitle: string;
    indicators: { tracked: string; pending: string; interviews: string; admitted: string };
    searchLabel: string;
    searchHint: string;
    searchPlaceholder: string;
    statusLabel: string;
    statusHint: string;
    allStatuses: string;
    establishmentLabel: string;
    allEstablishments: string;
    resultsCount: (count: number, total: number) => string;
    resetFilters: string;
    emptyTitle: string;
    emptyText: string;
    tableCaption: string;
    columns: { candidate: string; establishment: string; formation: string; status: string; updated: string };
    statuses: { pending: string; preinscribed: string; interview: string; admitted: string };
  };
}
