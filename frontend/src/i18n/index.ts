import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './en.json';
import ja from './ja.json';

const resources = {
    en: {
        translation: en
    },
    ja: {
        translation: ja
    }
};

i18n
    .use(initReactI18next)
    .init({
        resources,
        lng: localStorage.getItem('language') || 'en', // Get saved language or default to English
        fallbackLng: 'en',

        interpolation: {
            escapeValue: false // React already does escaping
        },

        // Enable debug mode in development
        debug: false
    });

export default i18n;