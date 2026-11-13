# Limites, dépannage et désinstallation

*[English below](#english)*

## Limites connues

- Chaque heure est partagée en deux demi-heures de même consommation. Une plage d'heures creuses qui commence à la demi-heure n'est donc suivie qu'approximativement dans cette heure.
- Les prix dynamiques (spot), les offres indexées sur le tarif réglementé et les jours spéciaux d'autres offres (Zen Flex…) ne sont pas encore pris en charge.
- Le client de l'API officielle de RTE n'a pas encore été testé sur l'API réelle.
- La page Contrats est en français ou en anglais, selon la langue de votre profil.

## Dépannage

- **La configuration réessaie sans cesse** : les tarifs ou les couleurs Tempo dont un contrat a besoin n'ont jamais pu être téléchargés. L'intégration réessaie toute seule ; l'erreur figure dans les journaux.
- **Réparation « Les couleurs Tempo ne se mettent plus à jour »** : le calendrier public de RTE échoue depuis deux jours. Ajoutez des identifiants RTE ([Configuration](configuration.md#compte-rte-facultatif)) pour que l'API officielle prenne le relais.
- **Réparation « RTE refuse les identifiants »** : vérifiez l'application sur data.rte-france.com et saisissez à nouveau les identifiants, ou effacez-les.
- **La page affiche « Préparation des calculs… »** : la source se recharge, au démarrage ou après un changement de contrat. Valoriser un nouveau contrat sur tout l'historique prend parfois quelques minutes ; la page se met à jour toute seule. Si cela dure, la page de l'intégration indique l'erreur.
- **Réparation « *contrat* n'a pas de prix pour le … »** : aucune période de prix de ce contrat ne couvre ce jour. Ajoutez la période qui manque.
- **Un contrat s'arrête à une date** : les comparaisons s'arrêtent avec lui. Ses diagnostics indiquent s'il attend une couleur ou un prix.
- **Journaux de débogage** : activez-les depuis le menu de l'intégration ; ils incluent la bibliothèque `elec_tariffs`.

## Désinstallation

1. **Paramètres → Appareils et services → Electricity Contracts**, ouvrez le menu de l'entrée et choisissez **Supprimer**. Ses statistiques, son cache et ses réparations sont supprimés avec elle, et la page Contrats quitte le menu avec la dernière source.
2. Pour retirer aussi le code, désinstallez-la dans HACS et redémarrez Home Assistant.

---

## English

- The consumption never leaves Home Assistant. Diagnostics hide the statistic ID, the entry title (both contain the meter number) and the RTE credentials.
- Hours are split into two half hours with the same consumption. Spot prices, offers indexed on the regulated prices and special days of other offers aren't supported yet. The official RTE API client hasn't been tested against the live API yet. The Contracts page is in French or English, following your profile's language.
- **Repairs**:
  - "Tempo colors can't be updated": add RTE credentials;
  - "RTE refuses the credentials": enter them again or clear them;
  - "*contract* has no price for …": no price period of this contract covers that day; add the missing one.

  A contract that stops at a date stops the comparisons with it: its diagnostics tell whether it waits for a color or a price.
- **"Preparing the figures…"** on the page: the source is reloading, at startup or after a change of contract. Costing a new contract over the whole history can take a few minutes; the page updates by itself. If it lasts, the integration's page shows the error.
- **Removal**: delete the entry from **Settings → Devices & services → Electricity Contracts**. Its statistics, cache and repairs go with it, and the Contracts page leaves the sidebar with the last source. Then uninstall it in HACS and restart.
