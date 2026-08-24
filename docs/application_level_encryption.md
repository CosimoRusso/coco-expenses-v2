# Application level encryption

To make impossible for the admin to read user expenses, we implement application level encryption.

## How it works

in the Expense model, description and amount have 2 associated fields: encrypted_description and encrypted_amount. These are used if in UserSettings the field is_encrypted=True.

The encryption key is derived from the password and set as a cookie, so that only the final user has it.

On registration, it is not possible to select encryption, but then it can be activated and deactivated from the user settings.

When registration is activated, a POST request to /activate-encryption is performed, the API call encrypts all user expenses using the user password (that must be sent along with the request, and is checked just like in a normal login). In the response, the server sets the user_crypto_key cookie, just like in the normal login of an encrypted user.

The encryption is transparent in the frontend (except for said cookie) cause all the decryption is performed in the backend.

On password change the new password must be used to re-encrypt all the data.

## TODO

- add a flag in user settings page to decide if user is encrypted.
- Make CRUD of expenses manage the encryption layer
- If user click on "encrypt my data" enxrypt all its expenses, Make user notice that a lost password means losing all data forever
- If user click on "decrypt my data" decrypt all its expenses.
- manage csv upload: if the user is encrypted all the expenses must be preprocessed and encrypted.
