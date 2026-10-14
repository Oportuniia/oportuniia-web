<?php
// Copy OUTSIDE public_html to /home/<hosting-user>/private/oportuniia-mail.php.
// Generate the shared key privately; same key in Render WEB_MAIL_BRIDGE_KEY.
// Do not enable until the mailbox, local MTA, sender/DKIM/SPF and bridge are tested.
return [
    'enabled' => false,
    'key' => '',
    'from' => 'info.web@oportuniia.com',
    'nonce_directory' => '/home/<hosting-user>/private/oportuniia-mail-nonces',
];
