Introduction
------------

L'API de la base SDBDKR CATECHESE offre un moyen simple d'intégrer des données provenant d'un système externe. L'API suit les principes d'architecture REST, utilise le format JSON pour encoder les données, s'appuie sur les codes HTTP standards et propose des messages d'erreurs à la fois techniques mais également lisibles par les humains pour signaler les dysfonctionnements.

Cette documentation est générée automatiquement à partir des table et des champs disponibles dans votre basse de données. Si vous effectuez des modifications sur la base, les tables ou bien sur les champs des tables, cela peut également modifier l'API. Par conséquent, assurez-vous de mettre à jour les clients de votre API dans ce cas.

L´identifiant de la base est : `117`  
Exemple JavaScript de la requête d'API : [axios](https://github.com/axios/axios)  
Exemple en Python de la requête d'API : [requests](https://requests.readthedocs.io/en/master/)

Authentification
----------------

Baserow utilise un système d'authentification simple par jeton. Vous devez générer au moins un jeton d'authentification dans votre compte afin d'utiliser les API suivantes. Il est possible de définir des droits de création, lecture, modification et suppression par table et ce pour chaque jeton. Pour vous authentifier, fournissez le jeton via l'entête HTTP « Authorization » de la requête. Tous les appels à l'API doivent être authentifiés et réalisés via le protocole sécurisé HTTPS.

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech"

Table Parents
-------------

L'identifiant de cette table est : `572`

### Champs

Chaque ligne dans la table « Parents » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_5445

Téléphone

`string`

`equal``not_equal``contains``contains_not``length_is_lower_than``empty``not_empty`

Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .

field\_5442

Prenoms

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5444

Actif

`boolean`

`boolean``empty``not_empty`

Accepte une valeur booléenne.

field\_5446

Code Parent

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5447

Nom

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5448

Téléphone 2

`string`

`equal``not_equal``contains``contains_not``length_is_lower_than``empty``not_empty`

Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .

field\_5449

Email

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une adresse électronique valide.

### Lister les champs

Afin de lister les champs de la table Parents une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/572/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/572/"

Example de réponse





    [
        {
            "id": 5445,
            "table_id": 572,
            "name": "Téléphone",
            "order": 3,
            "type": "phone_number",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5442,
            "table_id": 572,
            "name": "Prenoms",
            "order": 0,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5444,
            "table_id": 572,
            "name": "Actif",
            "order": 2,
            "type": "boolean",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Parents_ une requête de type `GET` doit être envoyée au point d'accès de la table _Parents_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/572/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/572/?user_field_names=true"

Example de réponse





field\_5445

field\_5442

field\_5444

field\_5446

field\_5447

field\_5448

field\_5449

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/572/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Téléphone": "+1-541-754-3010",
                "Prenoms": "string",
                "Actif": true,
                "Code Parent": "string",
                "Nom": "string",
                "Téléphone 2": "+1-541-754-3010",
                "Email": "example@baserow.io"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Parents.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row_id}/?user_field_names=true"

Example de réponse





field\_5445

field\_5442

field\_5444

field\_5446

field\_5447

field\_5448

field\_5449

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Téléphone": "+1-541-754-3010",
        "Prenoms": "string",
        "Actif": true,
        "Code Parent": "string",
        "Nom": "string",
        "Téléphone 2": "+1-541-754-3010",
        "Email": "example@baserow.io"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Parents.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Téléphone field\_5445
    
    optionnel
    
    `string`
    
    Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .
    
*   Prenoms field\_5442
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Actif field\_5444
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Code Parent field\_5446
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Nom field\_5447
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Téléphone 2 field\_5448
    
    optionnel
    
    `string`
    
    Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .
    
*   Email field\_5449
    
    optionnel
    
    `string`
    
    Accepte une adresse électronique valide.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/572/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5445

field\_5442

field\_5444

field\_5446

field\_5447

field\_5448

field\_5449

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/572/?user_field_names=true" \
    --data '{
        "Téléphone": "+1-541-754-3010",
        "Prenoms": "string",
        "Actif": true,
        "Code Parent": "string",
        "Nom": "string",
        "Téléphone 2": "+1-541-754-3010",
        "Email": "example@baserow.io"
    }'

Example de réponse





field\_5445

field\_5442

field\_5444

field\_5446

field\_5447

field\_5448

field\_5449

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Téléphone": "+1-541-754-3010",
        "Prenoms": "string",
        "Actif": true,
        "Code Parent": "string",
        "Nom": "string",
        "Téléphone 2": "+1-541-754-3010",
        "Email": "example@baserow.io"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Parents.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Téléphone field\_5445
    
    optionnel
    
    `string`
    
    Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .
    
*   Prenoms field\_5442
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Actif field\_5444
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Code Parent field\_5446
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Nom field\_5447
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Téléphone 2 field\_5448
    
    optionnel
    
    `string`
    
    Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .
    
*   Email field\_5449
    
    optionnel
    
    `string`
    
    Accepte une adresse électronique valide.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5445

field\_5442

field\_5444

field\_5446

field\_5447

field\_5448

field\_5449

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row_id}/?user_field_names=true" \
    --data '{
        "Téléphone": "+1-541-754-3010",
        "Prenoms": "string",
        "Actif": true,
        "Code Parent": "string",
        "Nom": "string",
        "Téléphone 2": "+1-541-754-3010",
        "Email": "example@baserow.io"
    }'

Example de réponse





field\_5445

field\_5442

field\_5444

field\_5446

field\_5447

field\_5448

field\_5449

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Téléphone": "+1-541-754-3010",
        "Prenoms": "string",
        "Actif": true,
        "Code Parent": "string",
        "Nom": "string",
        "Téléphone 2": "+1-541-754-3010",
        "Email": "example@baserow.io"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Parents_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row_id}/move/"

Example de réponse





field\_5445

field\_5442

field\_5444

field\_5446

field\_5447

field\_5448

field\_5449

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Téléphone": "+1-541-754-3010",
        "Prenoms": "string",
        "Actif": true,
        "Code Parent": "string",
        "Nom": "string",
        "Téléphone 2": "+1-541-754-3010",
        "Email": "example@baserow.io"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Parents\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/572/{row_id}/"

Table Inscriptions
------------------

L'identifiant de cette table est : `574`

### Champs

Chaque ligne dans la table « Inscriptions » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_5465

ID Inscription

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5466

ID Catechumene

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5467

Prenoms

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5468

Nom

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5469

AnneePrecedente

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5470

ParoisseAnneePrecedente

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5471

ClasseCourante

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5472

Montant

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_5473

Paye

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_5474

DateInscription

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date/heure au format ISO.

field\_5475

Commentaire

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5476

sms

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5477

action

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5478

AttestationDeTransfert

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5479

operateur

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5502

Annee Inscription

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6020

Resultat Final

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6021

Note Finale

`decimal`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un nombre décimal positif.

field\_6022

Moyen Paiement

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6023

Infos Paiement

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6024

Choix Paiement

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6025

Annee Suivante

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6026

Etat

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6027

Absennces

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6093

Livre Remis

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6154

ReconCheck

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6155

ReconOP

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6157

Groupe

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6510

ID\_ClasseCourante

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6512

ID\_AnneePrecedente

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6514

ID\_AnneeInscription

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 576. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6516

ID\_AnneeSuivante

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6525

Mouvements de caisse

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 694. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

### Lister les champs

Afin de lister les champs de la table Inscriptions une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/574/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/574/"

Example de réponse





    [
        {
            "id": 5465,
            "table_id": 574,
            "name": "ID Inscription",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5466,
            "table_id": 574,
            "name": "ID Catechumene",
            "order": 1,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5467,
            "table_id": 574,
            "name": "Prenoms",
            "order": 2,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Inscriptions_ une requête de type `GET` doit être envoyée au point d'accès de la table _Inscriptions_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user_field_names=true"

Example de réponse





field\_5465

field\_5466

field\_5467

field\_5468

field\_5469

field\_5470

field\_5471

field\_5472

field\_5473

field\_5474

field\_5475

field\_5476

field\_5477

field\_5478

field\_5479

field\_5502

field\_6020

field\_6021

field\_6022

field\_6023

field\_6024

field\_6025

field\_6026

field\_6027

field\_6093

field\_6154

field\_6155

field\_6157

field\_6510

field\_6512

field\_6514

field\_6516

field\_6525

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/574/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "ID Inscription": "string",
                "ID Catechumene": "string",
                "Prenoms": "string",
                "Nom": "string",
                "AnneePrecedente": "string",
                "ParoisseAnneePrecedente": "string",
                "ClasseCourante": "string",
                "Montant": 0,
                "Paye": 0,
                "DateInscription": "2020-01-01T12:00:00Z",
                "Commentaire": "string",
                "sms": "string",
                "action": "string",
                "AttestationDeTransfert": "string",
                "operateur": "string",
                "Annee Inscription": "string",
                "Resultat Final": "string",
                "Note Finale": "0.00",
                "Moyen Paiement": "string",
                "Infos Paiement": "string",
                "Choix Paiement": "string",
                "Annee Suivante": "string",
                "Etat": "string",
                "Absennces": 0,
                "Livre Remis": "string",
                "ReconCheck": "string",
                "ReconOP": "string",
                "Groupe": "string",
                "ID_ClasseCourante": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "ID_AnneePrecedente": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "ID_AnneeInscription": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "ID_AnneeSuivante": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "Mouvements de caisse": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Inscriptions.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row_id}/?user_field_names=true"

Example de réponse





field\_5465

field\_5466

field\_5467

field\_5468

field\_5469

field\_5470

field\_5471

field\_5472

field\_5473

field\_5474

field\_5475

field\_5476

field\_5477

field\_5478

field\_5479

field\_5502

field\_6020

field\_6021

field\_6022

field\_6023

field\_6024

field\_6025

field\_6026

field\_6027

field\_6093

field\_6154

field\_6155

field\_6157

field\_6510

field\_6512

field\_6514

field\_6516

field\_6525

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Inscription": "string",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "AnneePrecedente": "string",
        "ParoisseAnneePrecedente": "string",
        "ClasseCourante": "string",
        "Montant": 0,
        "Paye": 0,
        "DateInscription": "2020-01-01T12:00:00Z",
        "Commentaire": "string",
        "sms": "string",
        "action": "string",
        "AttestationDeTransfert": "string",
        "operateur": "string",
        "Annee Inscription": "string",
        "Resultat Final": "string",
        "Note Finale": "0.00",
        "Moyen Paiement": "string",
        "Infos Paiement": "string",
        "Choix Paiement": "string",
        "Annee Suivante": "string",
        "Etat": "string",
        "Absennces": 0,
        "Livre Remis": "string",
        "ReconCheck": "string",
        "ReconOP": "string",
        "Groupe": "string",
        "ID_ClasseCourante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneePrecedente": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeInscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Mouvements de caisse": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Inscriptions.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   ID Inscription field\_5465
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ID Catechumene field\_5466
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Prenoms field\_5467
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Nom field\_5468
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   AnneePrecedente field\_5469
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ParoisseAnneePrecedente field\_5470
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ClasseCourante field\_5471
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Montant field\_5472
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Paye field\_5473
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   DateInscription field\_5474
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Commentaire field\_5475
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   sms field\_5476
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   action field\_5477
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   AttestationDeTransfert field\_5478
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   operateur field\_5479
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Annee Inscription field\_5502
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Resultat Final field\_6020
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Note Finale field\_6021
    
    optionnel
    
    `decimal`
    
    Accepte un nombre décimal positif.
    
*   Moyen Paiement field\_6022
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Infos Paiement field\_6023
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Choix Paiement field\_6024
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Annee Suivante field\_6025
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Etat field\_6026
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Absennces field\_6027
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Livre Remis field\_6093
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ReconCheck field\_6154
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ReconOP field\_6155
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Groupe field\_6157
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ID\_ClasseCourante field\_6510
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   ID\_AnneePrecedente field\_6512
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   ID\_AnneeInscription field\_6514
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 576. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   ID\_AnneeSuivante field\_6516
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   Mouvements de caisse field\_6525
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 694. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5465

field\_5466

field\_5467

field\_5468

field\_5469

field\_5470

field\_5471

field\_5472

field\_5473

field\_5474

field\_5475

field\_5476

field\_5477

field\_5478

field\_5479

field\_5502

field\_6020

field\_6021

field\_6022

field\_6023

field\_6024

field\_6025

field\_6026

field\_6027

field\_6093

field\_6154

field\_6155

field\_6157

field\_6510

field\_6512

field\_6514

field\_6516

field\_6525

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user_field_names=true" \
    --data '{
        "ID Inscription": "string",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "AnneePrecedente": "string",
        "ParoisseAnneePrecedente": "string",
        "ClasseCourante": "string",
        "Montant": 0,
        "Paye": 0,
        "DateInscription": "2020-01-01T12:00:00Z",
        "Commentaire": "string",
        "sms": "string",
        "action": "string",
        "AttestationDeTransfert": "string",
        "operateur": "string",
        "Annee Inscription": "string",
        "Resultat Final": "string",
        "Note Finale": "0.00",
        "Moyen Paiement": "string",
        "Infos Paiement": "string",
        "Choix Paiement": "string",
        "Annee Suivante": "string",
        "Etat": "string",
        "Absennces": 0,
        "Livre Remis": "string",
        "ReconCheck": "string",
        "ReconOP": "string",
        "Groupe": "string",
        "ID_ClasseCourante": [
            1
        ],
        "ID_AnneePrecedente": [
            1
        ],
        "ID_AnneeInscription": [
            1
        ],
        "ID_AnneeSuivante": [
            1
        ],
        "Mouvements de caisse": [
            1
        ]
    }'

Example de réponse





field\_5465

field\_5466

field\_5467

field\_5468

field\_5469

field\_5470

field\_5471

field\_5472

field\_5473

field\_5474

field\_5475

field\_5476

field\_5477

field\_5478

field\_5479

field\_5502

field\_6020

field\_6021

field\_6022

field\_6023

field\_6024

field\_6025

field\_6026

field\_6027

field\_6093

field\_6154

field\_6155

field\_6157

field\_6510

field\_6512

field\_6514

field\_6516

field\_6525

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Inscription": "string",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "AnneePrecedente": "string",
        "ParoisseAnneePrecedente": "string",
        "ClasseCourante": "string",
        "Montant": 0,
        "Paye": 0,
        "DateInscription": "2020-01-01T12:00:00Z",
        "Commentaire": "string",
        "sms": "string",
        "action": "string",
        "AttestationDeTransfert": "string",
        "operateur": "string",
        "Annee Inscription": "string",
        "Resultat Final": "string",
        "Note Finale": "0.00",
        "Moyen Paiement": "string",
        "Infos Paiement": "string",
        "Choix Paiement": "string",
        "Annee Suivante": "string",
        "Etat": "string",
        "Absennces": 0,
        "Livre Remis": "string",
        "ReconCheck": "string",
        "ReconOP": "string",
        "Groupe": "string",
        "ID_ClasseCourante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneePrecedente": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeInscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Mouvements de caisse": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Inscriptions.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   ID Inscription field\_5465
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ID Catechumene field\_5466
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Prenoms field\_5467
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Nom field\_5468
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   AnneePrecedente field\_5469
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ParoisseAnneePrecedente field\_5470
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ClasseCourante field\_5471
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Montant field\_5472
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Paye field\_5473
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   DateInscription field\_5474
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Commentaire field\_5475
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   sms field\_5476
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   action field\_5477
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   AttestationDeTransfert field\_5478
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   operateur field\_5479
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Annee Inscription field\_5502
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Resultat Final field\_6020
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Note Finale field\_6021
    
    optionnel
    
    `decimal`
    
    Accepte un nombre décimal positif.
    
*   Moyen Paiement field\_6022
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Infos Paiement field\_6023
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Choix Paiement field\_6024
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Annee Suivante field\_6025
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Etat field\_6026
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Absennces field\_6027
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Livre Remis field\_6093
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ReconCheck field\_6154
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ReconOP field\_6155
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Groupe field\_6157
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ID\_ClasseCourante field\_6510
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   ID\_AnneePrecedente field\_6512
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   ID\_AnneeInscription field\_6514
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 576. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   ID\_AnneeSuivante field\_6516
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 661. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   Mouvements de caisse field\_6525
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 694. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5465

field\_5466

field\_5467

field\_5468

field\_5469

field\_5470

field\_5471

field\_5472

field\_5473

field\_5474

field\_5475

field\_5476

field\_5477

field\_5478

field\_5479

field\_5502

field\_6020

field\_6021

field\_6022

field\_6023

field\_6024

field\_6025

field\_6026

field\_6027

field\_6093

field\_6154

field\_6155

field\_6157

field\_6510

field\_6512

field\_6514

field\_6516

field\_6525

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row_id}/?user_field_names=true" \
    --data '{
        "ID Inscription": "string",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "AnneePrecedente": "string",
        "ParoisseAnneePrecedente": "string",
        "ClasseCourante": "string",
        "Montant": 0,
        "Paye": 0,
        "DateInscription": "2020-01-01T12:00:00Z",
        "Commentaire": "string",
        "sms": "string",
        "action": "string",
        "AttestationDeTransfert": "string",
        "operateur": "string",
        "Annee Inscription": "string",
        "Resultat Final": "string",
        "Note Finale": "0.00",
        "Moyen Paiement": "string",
        "Infos Paiement": "string",
        "Choix Paiement": "string",
        "Annee Suivante": "string",
        "Etat": "string",
        "Absennces": 0,
        "Livre Remis": "string",
        "ReconCheck": "string",
        "ReconOP": "string",
        "Groupe": "string",
        "ID_ClasseCourante": [
            1
        ],
        "ID_AnneePrecedente": [
            1
        ],
        "ID_AnneeInscription": [
            1
        ],
        "ID_AnneeSuivante": [
            1
        ],
        "Mouvements de caisse": [
            1
        ]
    }'

Example de réponse





field\_5465

field\_5466

field\_5467

field\_5468

field\_5469

field\_5470

field\_5471

field\_5472

field\_5473

field\_5474

field\_5475

field\_5476

field\_5477

field\_5478

field\_5479

field\_5502

field\_6020

field\_6021

field\_6022

field\_6023

field\_6024

field\_6025

field\_6026

field\_6027

field\_6093

field\_6154

field\_6155

field\_6157

field\_6510

field\_6512

field\_6514

field\_6516

field\_6525

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Inscription": "string",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "AnneePrecedente": "string",
        "ParoisseAnneePrecedente": "string",
        "ClasseCourante": "string",
        "Montant": 0,
        "Paye": 0,
        "DateInscription": "2020-01-01T12:00:00Z",
        "Commentaire": "string",
        "sms": "string",
        "action": "string",
        "AttestationDeTransfert": "string",
        "operateur": "string",
        "Annee Inscription": "string",
        "Resultat Final": "string",
        "Note Finale": "0.00",
        "Moyen Paiement": "string",
        "Infos Paiement": "string",
        "Choix Paiement": "string",
        "Annee Suivante": "string",
        "Etat": "string",
        "Absennces": 0,
        "Livre Remis": "string",
        "ReconCheck": "string",
        "ReconOP": "string",
        "Groupe": "string",
        "ID_ClasseCourante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneePrecedente": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeInscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Mouvements de caisse": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Inscriptions_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row_id}/move/"

Example de réponse





field\_5465

field\_5466

field\_5467

field\_5468

field\_5469

field\_5470

field\_5471

field\_5472

field\_5473

field\_5474

field\_5475

field\_5476

field\_5477

field\_5478

field\_5479

field\_5502

field\_6020

field\_6021

field\_6022

field\_6023

field\_6024

field\_6025

field\_6026

field\_6027

field\_6093

field\_6154

field\_6155

field\_6157

field\_6510

field\_6512

field\_6514

field\_6516

field\_6525

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Inscription": "string",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "AnneePrecedente": "string",
        "ParoisseAnneePrecedente": "string",
        "ClasseCourante": "string",
        "Montant": 0,
        "Paye": 0,
        "DateInscription": "2020-01-01T12:00:00Z",
        "Commentaire": "string",
        "sms": "string",
        "action": "string",
        "AttestationDeTransfert": "string",
        "operateur": "string",
        "Annee Inscription": "string",
        "Resultat Final": "string",
        "Note Finale": "0.00",
        "Moyen Paiement": "string",
        "Infos Paiement": "string",
        "Choix Paiement": "string",
        "Annee Suivante": "string",
        "Etat": "string",
        "Absennces": 0,
        "Livre Remis": "string",
        "ReconCheck": "string",
        "ReconOP": "string",
        "Groupe": "string",
        "ID_ClasseCourante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneePrecedente": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeInscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Mouvements de caisse": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Inscriptions\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/574/{row_id}/"

Table Catechumenes
------------------

L'identifiant de cette table est : `575`

### Champs

Chaque ligne dans la table « Catechumenes » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_5482

ID Catechumene

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5483

Prenoms

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5484

Nom

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5485

Baptisee

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5486

Extrait De Bapteme Fourni

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5487

LieuBapteme

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5488

Commentaire

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5489

Année de naissance

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5490

Attestation De Transfert Fournie

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5491

operateur

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5492

Code Parent

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5493

Extrait de Naissance Fourni

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

2773

oui

2774

non

field\_5494

Extrait Bapteme

`array`

`filename_contains``has_file_type``files_lower_than``empty``not_empty`

Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.

field\_5495

Extrait Naissance

`array`

`filename_contains``has_file_type``files_lower_than``empty``not_empty`

Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.

field\_5496

Attestation Transfert

`array`

`filename_contains``has_file_type``files_lower_than``empty``not_empty`

Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.

### Lister les champs

Afin de lister les champs de la table Catechumenes une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/575/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/575/"

Example de réponse





    [
        {
            "id": 5482,
            "table_id": 575,
            "name": "ID Catechumene",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5483,
            "table_id": 575,
            "name": "Prenoms",
            "order": 1,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5484,
            "table_id": 575,
            "name": "Nom",
            "order": 2,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Catechumenes_ une requête de type `GET` doit être envoyée au point d'accès de la table _Catechumenes_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user_field_names=true"

Example de réponse





field\_5482

field\_5483

field\_5484

field\_5485

field\_5486

field\_5487

field\_5488

field\_5489

field\_5490

field\_5491

field\_5492

field\_5493

field\_5494

field\_5495

field\_5496

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/575/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "ID Catechumene": "string",
                "Prenoms": "string",
                "Nom": "string",
                "Baptisee": "string",
                "Extrait De Bapteme Fourni": "string",
                "LieuBapteme": "string",
                "Commentaire": "string",
                "Année de naissance": "string",
                "Attestation De Transfert Fournie": "string",
                "operateur": "string",
                "Code Parent": "string",
                "Extrait de Naissance Fourni": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Extrait Bapteme": [
                    {
                        "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "thumbnails": {
                            "tiny": {
                                "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 21,
                                "height": 21
                            },
                            "small": {
                                "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 48,
                                "height": 48
                            }
                        },
                        "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "size": 229940,
                        "mime_type": "image/png",
                        "is_image": true,
                        "image_width": 1280,
                        "image_height": 585,
                        "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
                    }
                ],
                "Extrait Naissance": [
                    {
                        "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "thumbnails": {
                            "tiny": {
                                "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 21,
                                "height": 21
                            },
                            "small": {
                                "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 48,
                                "height": 48
                            }
                        },
                        "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "size": 229940,
                        "mime_type": "image/png",
                        "is_image": true,
                        "image_width": 1280,
                        "image_height": 585,
                        "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
                    }
                ],
                "Attestation Transfert": [
                    {
                        "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "thumbnails": {
                            "tiny": {
                                "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 21,
                                "height": 21
                            },
                            "small": {
                                "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 48,
                                "height": 48
                            }
                        },
                        "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "size": 229940,
                        "mime_type": "image/png",
                        "is_image": true,
                        "image_width": 1280,
                        "image_height": 585,
                        "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Catechumenes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row_id}/?user_field_names=true"

Example de réponse





field\_5482

field\_5483

field\_5484

field\_5485

field\_5486

field\_5487

field\_5488

field\_5489

field\_5490

field\_5491

field\_5492

field\_5493

field\_5494

field\_5495

field\_5496

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "Baptisee": "string",
        "Extrait De Bapteme Fourni": "string",
        "LieuBapteme": "string",
        "Commentaire": "string",
        "Année de naissance": "string",
        "Attestation De Transfert Fournie": "string",
        "operateur": "string",
        "Code Parent": "string",
        "Extrait de Naissance Fourni": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Extrait Bapteme": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Extrait Naissance": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Attestation Transfert": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Catechumenes.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   ID Catechumene field\_5482
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Prenoms field\_5483
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Nom field\_5484
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Baptisee field\_5485
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Extrait De Bapteme Fourni field\_5486
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   LieuBapteme field\_5487
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Commentaire field\_5488
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Année de naissance field\_5489
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Attestation De Transfert Fournie field\_5490
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   operateur field\_5491
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Code Parent field\_5492
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Extrait de Naissance Fourni field\_5493
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    2773
    
    oui
    
    2774
    
    non
    
*   Extrait Bapteme field\_5494
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    
*   Extrait Naissance field\_5495
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    
*   Attestation Transfert field\_5496
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5482

field\_5483

field\_5484

field\_5485

field\_5486

field\_5487

field\_5488

field\_5489

field\_5490

field\_5491

field\_5492

field\_5493

field\_5494

field\_5495

field\_5496

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user_field_names=true" \
    --data '{
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "Baptisee": "string",
        "Extrait De Bapteme Fourni": "string",
        "LieuBapteme": "string",
        "Commentaire": "string",
        "Année de naissance": "string",
        "Attestation De Transfert Fournie": "string",
        "operateur": "string",
        "Code Parent": "string",
        "Extrait de Naissance Fourni": 1,
        "Extrait Bapteme": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ],
        "Extrait Naissance": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ],
        "Attestation Transfert": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ]
    }'

Example de réponse





field\_5482

field\_5483

field\_5484

field\_5485

field\_5486

field\_5487

field\_5488

field\_5489

field\_5490

field\_5491

field\_5492

field\_5493

field\_5494

field\_5495

field\_5496

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "Baptisee": "string",
        "Extrait De Bapteme Fourni": "string",
        "LieuBapteme": "string",
        "Commentaire": "string",
        "Année de naissance": "string",
        "Attestation De Transfert Fournie": "string",
        "operateur": "string",
        "Code Parent": "string",
        "Extrait de Naissance Fourni": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Extrait Bapteme": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Extrait Naissance": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Attestation Transfert": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Catechumenes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   ID Catechumene field\_5482
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Prenoms field\_5483
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Nom field\_5484
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Baptisee field\_5485
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Extrait De Bapteme Fourni field\_5486
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   LieuBapteme field\_5487
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Commentaire field\_5488
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Année de naissance field\_5489
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Attestation De Transfert Fournie field\_5490
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   operateur field\_5491
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Code Parent field\_5492
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Extrait de Naissance Fourni field\_5493
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    2773
    
    oui
    
    2774
    
    non
    
*   Extrait Bapteme field\_5494
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    
*   Extrait Naissance field\_5495
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    
*   Attestation Transfert field\_5496
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5482

field\_5483

field\_5484

field\_5485

field\_5486

field\_5487

field\_5488

field\_5489

field\_5490

field\_5491

field\_5492

field\_5493

field\_5494

field\_5495

field\_5496

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row_id}/?user_field_names=true" \
    --data '{
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "Baptisee": "string",
        "Extrait De Bapteme Fourni": "string",
        "LieuBapteme": "string",
        "Commentaire": "string",
        "Année de naissance": "string",
        "Attestation De Transfert Fournie": "string",
        "operateur": "string",
        "Code Parent": "string",
        "Extrait de Naissance Fourni": 1,
        "Extrait Bapteme": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ],
        "Extrait Naissance": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ],
        "Attestation Transfert": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ]
    }'

Example de réponse





field\_5482

field\_5483

field\_5484

field\_5485

field\_5486

field\_5487

field\_5488

field\_5489

field\_5490

field\_5491

field\_5492

field\_5493

field\_5494

field\_5495

field\_5496

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "Baptisee": "string",
        "Extrait De Bapteme Fourni": "string",
        "LieuBapteme": "string",
        "Commentaire": "string",
        "Année de naissance": "string",
        "Attestation De Transfert Fournie": "string",
        "operateur": "string",
        "Code Parent": "string",
        "Extrait de Naissance Fourni": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Extrait Bapteme": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Extrait Naissance": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Attestation Transfert": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Catechumenes_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row_id}/move/"

Example de réponse





field\_5482

field\_5483

field\_5484

field\_5485

field\_5486

field\_5487

field\_5488

field\_5489

field\_5490

field\_5491

field\_5492

field\_5493

field\_5494

field\_5495

field\_5496

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "ID Catechumene": "string",
        "Prenoms": "string",
        "Nom": "string",
        "Baptisee": "string",
        "Extrait De Bapteme Fourni": "string",
        "LieuBapteme": "string",
        "Commentaire": "string",
        "Année de naissance": "string",
        "Attestation De Transfert Fournie": "string",
        "operateur": "string",
        "Code Parent": "string",
        "Extrait de Naissance Fourni": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Extrait Bapteme": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Extrait Naissance": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "Attestation Transfert": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Catechumenes\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/575/{row_id}/"

Table Annee Inscription
-----------------------

L'identifiant de cette table est : `576`

### Champs

Chaque ligne dans la table « Annee Inscription » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_5497

Label

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5500

Status

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

### Lister les champs

Afin de lister les champs de la table Annee Inscription une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/576/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/576/"

Example de réponse





    [
        {
            "id": 5497,
            "table_id": 576,
            "name": "Label",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5500,
            "table_id": 576,
            "name": "Status",
            "order": 3,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Annee Inscription_ une requête de type `GET` doit être envoyée au point d'accès de la table _Annee Inscription_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/576/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/576/?user_field_names=true"

Example de réponse





field\_5497

field\_5500

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/576/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Label": "string",
                "Status": "string"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Annee Inscription.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row_id}/?user_field_names=true"

Example de réponse





field\_5497

field\_5500

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Label": "string",
        "Status": "string"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Annee Inscription.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Label field\_5497
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Status field\_5500
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/576/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5497

field\_5500

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/576/?user_field_names=true" \
    --data '{
        "Label": "string",
        "Status": "string"
    }'

Example de réponse





field\_5497

field\_5500

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Label": "string",
        "Status": "string"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Annee Inscription.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Label field\_5497
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Status field\_5500
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5497

field\_5500

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row_id}/?user_field_names=true" \
    --data '{
        "Label": "string",
        "Status": "string"
    }'

Example de réponse





field\_5497

field\_5500

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Label": "string",
        "Status": "string"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Annee Inscription_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row_id}/move/"

Example de réponse





field\_5497

field\_5500

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Label": "string",
        "Status": "string"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Annee Inscription\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/576/{row_id}/"

Table Notes
-----------

L'identifiant de cette table est : `577`

### Champs

Chaque ligne dans la table « Notes » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_5504

IdNote

`autonumber`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole`

Un champ en lecture seule qui dont la valeur s'incrémente automatiquement pour chaque nouvelle ligne.

field\_5506

Type

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5507

Commentaire

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_5910

Note

`decimal`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un nombre décimal positif.

field\_6019

Id Inscription

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6403

SaisieAssistée

`boolean`

`boolean``empty``not_empty`

Accepte une valeur booléenne.

field\_6404

Matière

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6405

DateÉpreuve

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date au format ISO.

field\_6406

Période

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

### Lister les champs

Afin de lister les champs de la table Notes une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/577/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/577/"

Example de réponse





    [
        {
            "id": 5504,
            "table_id": 577,
            "name": "IdNote",
            "order": 0,
            "type": "autonumber",
            "primary": true,
            "read_only": true,
            "description": "A sample description"
        },
        {
            "id": 5506,
            "table_id": 577,
            "name": "Type",
            "order": 2,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5507,
            "table_id": 577,
            "name": "Commentaire",
            "order": 3,
            "type": "long_text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Notes_ une requête de type `GET` doit être envoyée au point d'accès de la table _Notes_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/577/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/577/?user_field_names=true"

Example de réponse





field\_5504

field\_5506

field\_5507

field\_5910

field\_6019

field\_6403

field\_6404

field\_6405

field\_6406

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/577/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "IdNote": "1",
                "Type": "string",
                "Commentaire": "string",
                "Note": "0.00",
                "Id Inscription": "string",
                "SaisieAssistée": true,
                "Matière": "string",
                "DateÉpreuve": "2020-01-01",
                "Période": "string"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Notes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row_id}/?user_field_names=true"

Example de réponse





field\_5504

field\_5506

field\_5507

field\_5910

field\_6019

field\_6403

field\_6404

field\_6405

field\_6406

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IdNote": "1",
        "Type": "string",
        "Commentaire": "string",
        "Note": "0.00",
        "Id Inscription": "string",
        "SaisieAssistée": true,
        "Matière": "string",
        "DateÉpreuve": "2020-01-01",
        "Période": "string"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Notes.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Type field\_5506
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Commentaire field\_5507
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Note field\_5910
    
    optionnel
    
    `decimal`
    
    Accepte un nombre décimal positif.
    
*   Id Inscription field\_6019
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SaisieAssistée field\_6403
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Matière field\_6404
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   DateÉpreuve field\_6405
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Période field\_6406
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/577/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5506

field\_5507

field\_5910

field\_6019

field\_6403

field\_6404

field\_6405

field\_6406

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/577/?user_field_names=true" \
    --data '{
        "Type": "string",
        "Commentaire": "string",
        "Note": "0.00",
        "Id Inscription": "string",
        "SaisieAssistée": true,
        "Matière": "string",
        "DateÉpreuve": "2020-01-01",
        "Période": "string"
    }'

Example de réponse





field\_5504

field\_5506

field\_5507

field\_5910

field\_6019

field\_6403

field\_6404

field\_6405

field\_6406

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IdNote": "1",
        "Type": "string",
        "Commentaire": "string",
        "Note": "0.00",
        "Id Inscription": "string",
        "SaisieAssistée": true,
        "Matière": "string",
        "DateÉpreuve": "2020-01-01",
        "Période": "string"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Notes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Type field\_5506
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Commentaire field\_5507
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Note field\_5910
    
    optionnel
    
    `decimal`
    
    Accepte un nombre décimal positif.
    
*   Id Inscription field\_6019
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SaisieAssistée field\_6403
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Matière field\_6404
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   DateÉpreuve field\_6405
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Période field\_6406
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5506

field\_5507

field\_5910

field\_6019

field\_6403

field\_6404

field\_6405

field\_6406

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row_id}/?user_field_names=true" \
    --data '{
        "Type": "string",
        "Commentaire": "string",
        "Note": "0.00",
        "Id Inscription": "string",
        "SaisieAssistée": true,
        "Matière": "string",
        "DateÉpreuve": "2020-01-01",
        "Période": "string"
    }'

Example de réponse





field\_5504

field\_5506

field\_5507

field\_5910

field\_6019

field\_6403

field\_6404

field\_6405

field\_6406

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IdNote": "1",
        "Type": "string",
        "Commentaire": "string",
        "Note": "0.00",
        "Id Inscription": "string",
        "SaisieAssistée": true,
        "Matière": "string",
        "DateÉpreuve": "2020-01-01",
        "Période": "string"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Notes_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row_id}/move/"

Example de réponse





field\_5504

field\_5506

field\_5507

field\_5910

field\_6019

field\_6403

field\_6404

field\_6405

field\_6406

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IdNote": "1",
        "Type": "string",
        "Commentaire": "string",
        "Note": "0.00",
        "Id Inscription": "string",
        "SaisieAssistée": true,
        "Matière": "string",
        "DateÉpreuve": "2020-01-01",
        "Période": "string"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Notes\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/577/{row_id}/"

Table Utilisateurs
------------------

L'identifiant de cette table est : `578`

### Champs

Chaque ligne dans la table « Utilisateurs » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_5511

Courriel

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une adresse électronique valide.

field\_5512

Mot de Passe

`bool`

`empty``not_empty`

Un champ en écriture seule qui contient un mot de passe haché. La valeur sera \`null\` s'il n'est pas défini, ou \`true\` s'il a été défini. Il accepte une chaîne de caractères pour le définir.

field\_5513

Actif

`boolean`

`boolean``empty``not_empty`

Accepte une valeur booléenne.

field\_5514

Liste déroulante

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

2782

Parent

2783

Catéchiste

2784

Aumônier

2785

Curé

2786

Secrétaire Curé

2787

Président

2788

Secrétaire Général

2789

Secrétaire Général Adjoint

2790

Trésorier

2791

Trésorier Adjoint

2792

Responsable Organisation

2793

Membre Organisation

2794

Responsable Relations Extérieures

2795

Resp. Ajoint Relations Extérieures

field\_5515

Prénoms et Nom

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_5660

Code Parent

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6531

SystemActivityLog

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 695. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6540

SystemActivityLog - CancelledBy

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 695. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6554

SMS\_Messages

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 696. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6565

SMS\_Campaigns

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 697. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6575

SMS\_Templates

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 698. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

### Lister les champs

Afin de lister les champs de la table Utilisateurs une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/578/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/578/"

Example de réponse





    [
        {
            "id": 5511,
            "table_id": 578,
            "name": "Courriel",
            "order": 0,
            "type": "email",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5512,
            "table_id": 578,
            "name": "Mot de Passe",
            "order": 1,
            "type": "password",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 5513,
            "table_id": 578,
            "name": "Actif",
            "order": 2,
            "type": "boolean",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Utilisateurs_ une requête de type `GET` doit être envoyée au point d'accès de la table _Utilisateurs_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/578/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/578/?user_field_names=true"

Example de réponse





field\_5511

field\_5512

field\_5513

field\_5514

field\_5515

field\_5660

field\_6531

field\_6540

field\_6554

field\_6565

field\_6575

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/578/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Courriel": "example@baserow.io",
                "Mot de Passe": "true",
                "Actif": true,
                "Liste déroulante": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Prénoms et Nom": "string",
                "Code Parent": "string",
                "SystemActivityLog": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "SystemActivityLog - CancelledBy": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "SMS_Messages": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "SMS_Campaigns": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "SMS_Templates": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Utilisateurs.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row_id}/?user_field_names=true"

Example de réponse





field\_5511

field\_5512

field\_5513

field\_5514

field\_5515

field\_5660

field\_6531

field\_6540

field\_6554

field\_6565

field\_6575

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Courriel": "example@baserow.io",
        "Mot de Passe": "true",
        "Actif": true,
        "Liste déroulante": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Prénoms et Nom": "string",
        "Code Parent": "string",
        "SystemActivityLog": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SystemActivityLog - CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Templates": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Utilisateurs.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Courriel field\_5511
    
    optionnel
    
    `string`
    
    Accepte une adresse électronique valide.
    
*   Mot de Passe field\_5512
    
    optionnel
    
    `bool`
    
    Un champ en écriture seule qui contient un mot de passe haché. La valeur sera \`null\` s'il n'est pas défini, ou \`true\` s'il a été défini. Il accepte une chaîne de caractères pour le définir.
    
*   Actif field\_5513
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Liste déroulante field\_5514
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    2782
    
    Parent
    
    2783
    
    Catéchiste
    
    2784
    
    Aumônier
    
    2785
    
    Curé
    
    2786
    
    Secrétaire Curé
    
    2787
    
    Président
    
    2788
    
    Secrétaire Général
    
    2789
    
    Secrétaire Général Adjoint
    
    2790
    
    Trésorier
    
    2791
    
    Trésorier Adjoint
    
    2792
    
    Responsable Organisation
    
    2793
    
    Membre Organisation
    
    2794
    
    Responsable Relations Extérieures
    
    2795
    
    Resp. Ajoint Relations Extérieures
    
*   Prénoms et Nom field\_5515
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Code Parent field\_5660
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SystemActivityLog field\_6531
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 695. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SystemActivityLog - CancelledBy field\_6540
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 695. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Messages field\_6554
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 696. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Campaigns field\_6565
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 697. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Templates field\_6575
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 698. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/578/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5511

field\_5512

field\_5513

field\_5514

field\_5515

field\_5660

field\_6531

field\_6540

field\_6554

field\_6565

field\_6575

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/578/?user_field_names=true" \
    --data '{
        "Courriel": "example@baserow.io",
        "Mot de Passe": "true",
        "Actif": true,
        "Liste déroulante": 1,
        "Prénoms et Nom": "string",
        "Code Parent": "string",
        "SystemActivityLog": [
            1
        ],
        "SystemActivityLog - CancelledBy": [
            1
        ],
        "SMS_Messages": [
            1
        ],
        "SMS_Campaigns": [
            1
        ],
        "SMS_Templates": [
            1
        ]
    }'

Example de réponse





field\_5511

field\_5512

field\_5513

field\_5514

field\_5515

field\_5660

field\_6531

field\_6540

field\_6554

field\_6565

field\_6575

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Courriel": "example@baserow.io",
        "Mot de Passe": "true",
        "Actif": true,
        "Liste déroulante": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Prénoms et Nom": "string",
        "Code Parent": "string",
        "SystemActivityLog": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SystemActivityLog - CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Templates": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Utilisateurs.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Courriel field\_5511
    
    optionnel
    
    `string`
    
    Accepte une adresse électronique valide.
    
*   Mot de Passe field\_5512
    
    optionnel
    
    `bool`
    
    Un champ en écriture seule qui contient un mot de passe haché. La valeur sera \`null\` s'il n'est pas défini, ou \`true\` s'il a été défini. Il accepte une chaîne de caractères pour le définir.
    
*   Actif field\_5513
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Liste déroulante field\_5514
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    2782
    
    Parent
    
    2783
    
    Catéchiste
    
    2784
    
    Aumônier
    
    2785
    
    Curé
    
    2786
    
    Secrétaire Curé
    
    2787
    
    Président
    
    2788
    
    Secrétaire Général
    
    2789
    
    Secrétaire Général Adjoint
    
    2790
    
    Trésorier
    
    2791
    
    Trésorier Adjoint
    
    2792
    
    Responsable Organisation
    
    2793
    
    Membre Organisation
    
    2794
    
    Responsable Relations Extérieures
    
    2795
    
    Resp. Ajoint Relations Extérieures
    
*   Prénoms et Nom field\_5515
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Code Parent field\_5660
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SystemActivityLog field\_6531
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 695. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SystemActivityLog - CancelledBy field\_6540
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 695. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Messages field\_6554
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 696. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Campaigns field\_6565
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 697. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Templates field\_6575
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 698. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_5511

field\_5512

field\_5513

field\_5514

field\_5515

field\_5660

field\_6531

field\_6540

field\_6554

field\_6565

field\_6575

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row_id}/?user_field_names=true" \
    --data '{
        "Courriel": "example@baserow.io",
        "Mot de Passe": "true",
        "Actif": true,
        "Liste déroulante": 1,
        "Prénoms et Nom": "string",
        "Code Parent": "string",
        "SystemActivityLog": [
            1
        ],
        "SystemActivityLog - CancelledBy": [
            1
        ],
        "SMS_Messages": [
            1
        ],
        "SMS_Campaigns": [
            1
        ],
        "SMS_Templates": [
            1
        ]
    }'

Example de réponse





field\_5511

field\_5512

field\_5513

field\_5514

field\_5515

field\_5660

field\_6531

field\_6540

field\_6554

field\_6565

field\_6575

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Courriel": "example@baserow.io",
        "Mot de Passe": "true",
        "Actif": true,
        "Liste déroulante": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Prénoms et Nom": "string",
        "Code Parent": "string",
        "SystemActivityLog": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SystemActivityLog - CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Templates": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Utilisateurs_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row_id}/move/"

Example de réponse





field\_5511

field\_5512

field\_5513

field\_5514

field\_5515

field\_5660

field\_6531

field\_6540

field\_6554

field\_6565

field\_6575

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Courriel": "example@baserow.io",
        "Mot de Passe": "true",
        "Actif": true,
        "Liste déroulante": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Prénoms et Nom": "string",
        "Code Parent": "string",
        "SystemActivityLog": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SystemActivityLog - CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Templates": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Utilisateurs\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/578/{row_id}/"

Table ExtraitDeBapteme
----------------------

L'identifiant de cette table est : `657`

### Champs

Chaque ligne dans la table « ExtraitDeBapteme » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6221

IDCatechumene

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6223

Numéro Registre

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6224

Date Bapteme

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date au format ISO.

field\_6225

Fichier

`array`

`filename_contains``has_file_type``files_lower_than``empty``not_empty`

Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.

field\_6226

IDEB

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

### Lister les champs

Afin de lister les champs de la table ExtraitDeBapteme une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/657/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/657/"

Example de réponse





    [
        {
            "id": 6221,
            "table_id": 657,
            "name": "IDCatechumene",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6223,
            "table_id": 657,
            "name": "Numéro Registre",
            "order": 2,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6224,
            "table_id": 657,
            "name": "Date Bapteme",
            "order": 3,
            "type": "date",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _ExtraitDeBapteme_ une requête de type `GET` doit être envoyée au point d'accès de la table _ExtraitDeBapteme_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/657/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/657/?user_field_names=true"

Example de réponse





field\_6221

field\_6223

field\_6224

field\_6225

field\_6226

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/657/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "IDCatechumene": "string",
                "Numéro Registre": "string",
                "Date Bapteme": "2020-01-01",
                "Fichier": [
                    {
                        "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "thumbnails": {
                            "tiny": {
                                "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 21,
                                "height": 21
                            },
                            "small": {
                                "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 48,
                                "height": 48
                            }
                        },
                        "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "size": 229940,
                        "mime_type": "image/png",
                        "is_image": true,
                        "image_width": 1280,
                        "image_height": 585,
                        "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
                    }
                ],
                "IDEB": "string"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table ExtraitDeBapteme.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row_id}/?user_field_names=true"

Example de réponse





field\_6221

field\_6223

field\_6224

field\_6225

field\_6226

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IDCatechumene": "string",
        "Numéro Registre": "string",
        "Date Bapteme": "2020-01-01",
        "Fichier": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "IDEB": "string"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table ExtraitDeBapteme.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   IDCatechumene field\_6221
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Numéro Registre field\_6223
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Date Bapteme field\_6224
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Fichier field\_6225
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    
*   IDEB field\_6226
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/657/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6221

field\_6223

field\_6224

field\_6225

field\_6226

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/657/?user_field_names=true" \
    --data '{
        "IDCatechumene": "string",
        "Numéro Registre": "string",
        "Date Bapteme": "2020-01-01",
        "Fichier": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ],
        "IDEB": "string"
    }'

Example de réponse





field\_6221

field\_6223

field\_6224

field\_6225

field\_6226

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IDCatechumene": "string",
        "Numéro Registre": "string",
        "Date Bapteme": "2020-01-01",
        "Fichier": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "IDEB": "string"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table ExtraitDeBapteme.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   IDCatechumene field\_6221
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Numéro Registre field\_6223
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Date Bapteme field\_6224
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Fichier field\_6225
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    
*   IDEB field\_6226
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6221

field\_6223

field\_6224

field\_6225

field\_6226

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row_id}/?user_field_names=true" \
    --data '{
        "IDCatechumene": "string",
        "Numéro Registre": "string",
        "Date Bapteme": "2020-01-01",
        "Fichier": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ],
        "IDEB": "string"
    }'

Example de réponse





field\_6221

field\_6223

field\_6224

field\_6225

field\_6226

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IDCatechumene": "string",
        "Numéro Registre": "string",
        "Date Bapteme": "2020-01-01",
        "Fichier": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "IDEB": "string"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _ExtraitDeBapteme_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row_id}/move/"

Example de réponse





field\_6221

field\_6223

field\_6224

field\_6225

field\_6226

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "IDCatechumene": "string",
        "Numéro Registre": "string",
        "Date Bapteme": "2020-01-01",
        "Fichier": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ],
        "IDEB": "string"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*ExtraitDeBapteme\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/657/{row_id}/"

Table Classes
-------------

L'identifiant de cette table est : `661`

### Champs

Chaque ligne dans la table « Classes » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6243

Nom

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6244

court

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6245

Actif

`boolean`

`boolean``empty``not_empty`

Accepte une valeur booléenne.

field\_6509

Ordre

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6517

Inscriptions - ID\_AnneeSuivante

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 574. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

### Lister les champs

Afin de lister les champs de la table Classes une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/661/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/661/"

Example de réponse





    [
        {
            "id": 6243,
            "table_id": 661,
            "name": "Nom",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6244,
            "table_id": 661,
            "name": "court",
            "order": 1,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6245,
            "table_id": 661,
            "name": "Actif",
            "order": 2,
            "type": "boolean",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Classes_ une requête de type `GET` doit être envoyée au point d'accès de la table _Classes_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/661/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/661/?user_field_names=true"

Example de réponse





field\_6243

field\_6244

field\_6245

field\_6509

field\_6517

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/661/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Nom": "string",
                "court": "string",
                "Actif": true,
                "Ordre": 0,
                "Inscriptions - ID_AnneeSuivante": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Classes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row_id}/?user_field_names=true"

Example de réponse





field\_6243

field\_6244

field\_6245

field\_6509

field\_6517

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "court": "string",
        "Actif": true,
        "Ordre": 0,
        "Inscriptions - ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Classes.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Nom field\_6243
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   court field\_6244
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Actif field\_6245
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Ordre field\_6509
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Inscriptions - ID\_AnneeSuivante field\_6517
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 574. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/661/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6243

field\_6244

field\_6245

field\_6509

field\_6517

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/661/?user_field_names=true" \
    --data '{
        "Nom": "string",
        "court": "string",
        "Actif": true,
        "Ordre": 0,
        "Inscriptions - ID_AnneeSuivante": [
            1
        ]
    }'

Example de réponse





field\_6243

field\_6244

field\_6245

field\_6509

field\_6517

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "court": "string",
        "Actif": true,
        "Ordre": 0,
        "Inscriptions - ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Classes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Nom field\_6243
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   court field\_6244
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Actif field\_6245
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   Ordre field\_6509
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Inscriptions - ID\_AnneeSuivante field\_6517
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 574. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6243

field\_6244

field\_6245

field\_6509

field\_6517

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row_id}/?user_field_names=true" \
    --data '{
        "Nom": "string",
        "court": "string",
        "Actif": true,
        "Ordre": 0,
        "Inscriptions - ID_AnneeSuivante": [
            1
        ]
    }'

Example de réponse





field\_6243

field\_6244

field\_6245

field\_6509

field\_6517

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "court": "string",
        "Actif": true,
        "Ordre": 0,
        "Inscriptions - ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Classes_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row_id}/move/"

Example de réponse





field\_6243

field\_6244

field\_6245

field\_6509

field\_6517

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "court": "string",
        "Actif": true,
        "Ordre": 0,
        "Inscriptions - ID_AnneeSuivante": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Classes\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/661/{row_id}/"

Table MagicLinks
----------------

L'identifiant de cette table est : `678`

### Champs

Chaque ligne dans la table « MagicLinks » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6388

Hash

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6389

ExpireAt

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date/heure au format ISO.

field\_6390

Revoked

`boolean`

`boolean``empty``not_empty`

Accepte une valeur booléenne.

field\_6391

LastOpened

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date/heure au format ISO.

field\_6392

Id Inscription

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6393

OpenCount

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6394

Phone

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6395

ParentName

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6396

StudentName

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

### Lister les champs

Afin de lister les champs de la table MagicLinks une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/678/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/678/"

Example de réponse





    [
        {
            "id": 6388,
            "table_id": 678,
            "name": "Hash",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6389,
            "table_id": 678,
            "name": "ExpireAt",
            "order": 1,
            "type": "date",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6390,
            "table_id": 678,
            "name": "Revoked",
            "order": 2,
            "type": "boolean",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _MagicLinks_ une requête de type `GET` doit être envoyée au point d'accès de la table _MagicLinks_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/678/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/678/?user_field_names=true"

Example de réponse





field\_6388

field\_6389

field\_6390

field\_6391

field\_6392

field\_6393

field\_6394

field\_6395

field\_6396

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/678/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Hash": "string",
                "ExpireAt": "2020-01-01T12:00:00Z",
                "Revoked": true,
                "LastOpened": "2020-01-01T12:00:00Z",
                "Id Inscription": "string",
                "OpenCount": 0,
                "Phone": "string",
                "ParentName": "string",
                "StudentName": "string"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table MagicLinks.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row_id}/?user_field_names=true"

Example de réponse





field\_6388

field\_6389

field\_6390

field\_6391

field\_6392

field\_6393

field\_6394

field\_6395

field\_6396

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Hash": "string",
        "ExpireAt": "2020-01-01T12:00:00Z",
        "Revoked": true,
        "LastOpened": "2020-01-01T12:00:00Z",
        "Id Inscription": "string",
        "OpenCount": 0,
        "Phone": "string",
        "ParentName": "string",
        "StudentName": "string"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table MagicLinks.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Hash field\_6388
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ExpireAt field\_6389
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Revoked field\_6390
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   LastOpened field\_6391
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Id Inscription field\_6392
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   OpenCount field\_6393
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Phone field\_6394
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ParentName field\_6395
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   StudentName field\_6396
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/678/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6388

field\_6389

field\_6390

field\_6391

field\_6392

field\_6393

field\_6394

field\_6395

field\_6396

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/678/?user_field_names=true" \
    --data '{
        "Hash": "string",
        "ExpireAt": "2020-01-01T12:00:00Z",
        "Revoked": true,
        "LastOpened": "2020-01-01T12:00:00Z",
        "Id Inscription": "string",
        "OpenCount": 0,
        "Phone": "string",
        "ParentName": "string",
        "StudentName": "string"
    }'

Example de réponse





field\_6388

field\_6389

field\_6390

field\_6391

field\_6392

field\_6393

field\_6394

field\_6395

field\_6396

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Hash": "string",
        "ExpireAt": "2020-01-01T12:00:00Z",
        "Revoked": true,
        "LastOpened": "2020-01-01T12:00:00Z",
        "Id Inscription": "string",
        "OpenCount": 0,
        "Phone": "string",
        "ParentName": "string",
        "StudentName": "string"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table MagicLinks.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Hash field\_6388
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ExpireAt field\_6389
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Revoked field\_6390
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   LastOpened field\_6391
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Id Inscription field\_6392
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   OpenCount field\_6393
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Phone field\_6394
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   ParentName field\_6395
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   StudentName field\_6396
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6388

field\_6389

field\_6390

field\_6391

field\_6392

field\_6393

field\_6394

field\_6395

field\_6396

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row_id}/?user_field_names=true" \
    --data '{
        "Hash": "string",
        "ExpireAt": "2020-01-01T12:00:00Z",
        "Revoked": true,
        "LastOpened": "2020-01-01T12:00:00Z",
        "Id Inscription": "string",
        "OpenCount": 0,
        "Phone": "string",
        "ParentName": "string",
        "StudentName": "string"
    }'

Example de réponse





field\_6388

field\_6389

field\_6390

field\_6391

field\_6392

field\_6393

field\_6394

field\_6395

field\_6396

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Hash": "string",
        "ExpireAt": "2020-01-01T12:00:00Z",
        "Revoked": true,
        "LastOpened": "2020-01-01T12:00:00Z",
        "Id Inscription": "string",
        "OpenCount": 0,
        "Phone": "string",
        "ParentName": "string",
        "StudentName": "string"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _MagicLinks_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row_id}/move/"

Example de réponse





field\_6388

field\_6389

field\_6390

field\_6391

field\_6392

field\_6393

field\_6394

field\_6395

field\_6396

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Hash": "string",
        "ExpireAt": "2020-01-01T12:00:00Z",
        "Revoked": true,
        "LastOpened": "2020-01-01T12:00:00Z",
        "Id Inscription": "string",
        "OpenCount": 0,
        "Phone": "string",
        "ParentName": "string",
        "StudentName": "string"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*MagicLinks\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/678/{row_id}/"

Table LogsLLM
-------------

L'identifiant de cette table est : `679`

### Champs

Chaque ligne dans la table « LogsLLM » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6397

UserId

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6398

PayloadIn

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6399

PayloadOut

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6400

LatencyMs

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6401

CreatedAt

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date/heure au format ISO.

field\_6402

Operation

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

### Lister les champs

Afin de lister les champs de la table LogsLLM une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/679/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/679/"

Example de réponse





    [
        {
            "id": 6397,
            "table_id": 679,
            "name": "UserId",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6398,
            "table_id": 679,
            "name": "PayloadIn",
            "order": 1,
            "type": "long_text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6399,
            "table_id": 679,
            "name": "PayloadOut",
            "order": 2,
            "type": "long_text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _LogsLLM_ une requête de type `GET` doit être envoyée au point d'accès de la table _LogsLLM_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/679/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/679/?user_field_names=true"

Example de réponse





field\_6397

field\_6398

field\_6399

field\_6400

field\_6401

field\_6402

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/679/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "UserId": "string",
                "PayloadIn": "string",
                "PayloadOut": "string",
                "LatencyMs": 0,
                "CreatedAt": "2020-01-01T12:00:00Z",
                "Operation": "string"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table LogsLLM.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row_id}/?user_field_names=true"

Example de réponse





field\_6397

field\_6398

field\_6399

field\_6400

field\_6401

field\_6402

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "UserId": "string",
        "PayloadIn": "string",
        "PayloadOut": "string",
        "LatencyMs": 0,
        "CreatedAt": "2020-01-01T12:00:00Z",
        "Operation": "string"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table LogsLLM.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   UserId field\_6397
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   PayloadIn field\_6398
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   PayloadOut field\_6399
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   LatencyMs field\_6400
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   CreatedAt field\_6401
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Operation field\_6402
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/679/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6397

field\_6398

field\_6399

field\_6400

field\_6401

field\_6402

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/679/?user_field_names=true" \
    --data '{
        "UserId": "string",
        "PayloadIn": "string",
        "PayloadOut": "string",
        "LatencyMs": 0,
        "CreatedAt": "2020-01-01T12:00:00Z",
        "Operation": "string"
    }'

Example de réponse





field\_6397

field\_6398

field\_6399

field\_6400

field\_6401

field\_6402

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "UserId": "string",
        "PayloadIn": "string",
        "PayloadOut": "string",
        "LatencyMs": 0,
        "CreatedAt": "2020-01-01T12:00:00Z",
        "Operation": "string"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table LogsLLM.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   UserId field\_6397
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   PayloadIn field\_6398
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   PayloadOut field\_6399
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   LatencyMs field\_6400
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   CreatedAt field\_6401
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   Operation field\_6402
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6397

field\_6398

field\_6399

field\_6400

field\_6401

field\_6402

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row_id}/?user_field_names=true" \
    --data '{
        "UserId": "string",
        "PayloadIn": "string",
        "PayloadOut": "string",
        "LatencyMs": 0,
        "CreatedAt": "2020-01-01T12:00:00Z",
        "Operation": "string"
    }'

Example de réponse





field\_6397

field\_6398

field\_6399

field\_6400

field\_6401

field\_6402

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "UserId": "string",
        "PayloadIn": "string",
        "PayloadOut": "string",
        "LatencyMs": 0,
        "CreatedAt": "2020-01-01T12:00:00Z",
        "Operation": "string"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _LogsLLM_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row_id}/move/"

Example de réponse





field\_6397

field\_6398

field\_6399

field\_6400

field\_6401

field\_6402

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "UserId": "string",
        "PayloadIn": "string",
        "PayloadOut": "string",
        "LatencyMs": 0,
        "CreatedAt": "2020-01-01T12:00:00Z",
        "Operation": "string"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*LogsLLM\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/679/{row_id}/"

Table Types\_Notes
------------------

L'identifiant de cette table est : `680`

### Champs

Chaque ligne dans la table « Types\_Notes » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6407

Code

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6408

Libelle

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6409

Couleur

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

### Lister les champs

Afin de lister les champs de la table Types\_Notes une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/680/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/680/"

Example de réponse





    [
        {
            "id": 6407,
            "table_id": 680,
            "name": "Code",
            "order": 0,
            "type": "number",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6408,
            "table_id": 680,
            "name": "Libelle",
            "order": 1,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6409,
            "table_id": 680,
            "name": "Couleur",
            "order": 2,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Types\_Notes_ une requête de type `GET` doit être envoyée au point d'accès de la table _Types\_Notes_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/680/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/680/?user_field_names=true"

Example de réponse





field\_6407

field\_6408

field\_6409

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/680/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Code": 0,
                "Libelle": "string",
                "Couleur": "string"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Types\_Notes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row_id}/?user_field_names=true"

Example de réponse





field\_6407

field\_6408

field\_6409

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Couleur": "string"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Types\_Notes.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Code field\_6407
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Libelle field\_6408
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Couleur field\_6409
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/680/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6407

field\_6408

field\_6409

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/680/?user_field_names=true" \
    --data '{
        "Code": 0,
        "Libelle": "string",
        "Couleur": "string"
    }'

Example de réponse





field\_6407

field\_6408

field\_6409

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Couleur": "string"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Types\_Notes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Code field\_6407
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Libelle field\_6408
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Couleur field\_6409
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6407

field\_6408

field\_6409

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row_id}/?user_field_names=true" \
    --data '{
        "Code": 0,
        "Libelle": "string",
        "Couleur": "string"
    }'

Example de réponse





field\_6407

field\_6408

field\_6409

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Couleur": "string"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Types\_Notes_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row_id}/move/"

Example de réponse





field\_6407

field\_6408

field\_6409

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Couleur": "string"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Types\_Notes\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/680/{row_id}/"

Table Periodes
--------------

L'identifiant de cette table est : `681`

### Champs

Chaque ligne dans la table « Periodes » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6410

Code

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6411

Libelle

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6412

Annee\_Scolaire

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

### Lister les champs

Afin de lister les champs de la table Periodes une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/681/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/681/"

Example de réponse





    [
        {
            "id": 6410,
            "table_id": 681,
            "name": "Code",
            "order": 0,
            "type": "number",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6411,
            "table_id": 681,
            "name": "Libelle",
            "order": 1,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6412,
            "table_id": 681,
            "name": "Annee_Scolaire",
            "order": 2,
            "type": "text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Periodes_ une requête de type `GET` doit être envoyée au point d'accès de la table _Periodes_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/681/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/681/?user_field_names=true"

Example de réponse





field\_6410

field\_6411

field\_6412

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/681/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Code": 0,
                "Libelle": "string",
                "Annee_Scolaire": "string"
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Periodes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row_id}/?user_field_names=true"

Example de réponse





field\_6410

field\_6411

field\_6412

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Annee_Scolaire": "string"
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Periodes.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Code field\_6410
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Libelle field\_6411
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Annee\_Scolaire field\_6412
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/681/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6410

field\_6411

field\_6412

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/681/?user_field_names=true" \
    --data '{
        "Code": 0,
        "Libelle": "string",
        "Annee_Scolaire": "string"
    }'

Example de réponse





field\_6410

field\_6411

field\_6412

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Annee_Scolaire": "string"
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Periodes.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Code field\_6410
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Libelle field\_6411
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Annee\_Scolaire field\_6412
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6410

field\_6411

field\_6412

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row_id}/?user_field_names=true" \
    --data '{
        "Code": 0,
        "Libelle": "string",
        "Annee_Scolaire": "string"
    }'

Example de réponse





field\_6410

field\_6411

field\_6412

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Annee_Scolaire": "string"
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Periodes_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row_id}/move/"

Example de réponse





field\_6410

field\_6411

field\_6412

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Code": 0,
        "Libelle": "string",
        "Annee_Scolaire": "string"
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Periodes\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/681/{row_id}/"

Table Mouvements de caisse
--------------------------

L'identifiant de cette table est : `694`

### Champs

Chaque ligne dans la table « Mouvements de caisse » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6518

Nom

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6519

Date

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date au format ISO.

field\_6520

Type

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3306

Entrée

3307

Sortie

field\_6521

Catégorie

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3308

Inscription

3309

Don

3310

Matériel

3311

Transport

3312

Nourriture

3313

Divers

3353

Sacrement

field\_6522

Description

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6523

Montant

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6524

Inscription

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 574. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6526

Type de justificatif

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3314

Reçu

3315

Facture

3316

Ticket

3317

Sans justificatif

3318

Autre

field\_6527

Pièce justificative

`array`

`filename_contains``has_file_type``files_lower_than``empty``not_empty`

Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.

### Lister les champs

Afin de lister les champs de la table Mouvements de caisse une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/694/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/694/"

Example de réponse





    [
        {
            "id": 6518,
            "table_id": 694,
            "name": "Nom",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6519,
            "table_id": 694,
            "name": "Date",
            "order": 1,
            "type": "date",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6520,
            "table_id": 694,
            "name": "Type",
            "order": 2,
            "type": "single_select",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _Mouvements de caisse_ une requête de type `GET` doit être envoyée au point d'accès de la table _Mouvements de caisse_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/694/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/694/?user_field_names=true"

Example de réponse





field\_6518

field\_6519

field\_6520

field\_6521

field\_6522

field\_6523

field\_6524

field\_6526

field\_6527

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/694/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Nom": "string",
                "Date": "2020-01-01",
                "Type": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Catégorie": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Description": "string",
                "Montant": 0,
                "Inscription": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "Type de justificatif": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Pièce justificative": [
                    {
                        "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "thumbnails": {
                            "tiny": {
                                "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 21,
                                "height": 21
                            },
                            "small": {
                                "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                                "width": 48,
                                "height": 48
                            }
                        },
                        "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "size": 229940,
                        "mime_type": "image/png",
                        "is_image": true,
                        "image_width": 1280,
                        "image_height": 585,
                        "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table Mouvements de caisse.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row_id}/?user_field_names=true"

Example de réponse





field\_6518

field\_6519

field\_6520

field\_6521

field\_6522

field\_6523

field\_6524

field\_6526

field\_6527

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "Date": "2020-01-01",
        "Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Catégorie": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Description": "string",
        "Montant": 0,
        "Inscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Type de justificatif": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Pièce justificative": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table Mouvements de caisse.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Nom field\_6518
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Date field\_6519
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Type field\_6520
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3306
    
    Entrée
    
    3307
    
    Sortie
    
*   Catégorie field\_6521
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3308
    
    Inscription
    
    3309
    
    Don
    
    3310
    
    Matériel
    
    3311
    
    Transport
    
    3312
    
    Nourriture
    
    3313
    
    Divers
    
    3353
    
    Sacrement
    
*   Description field\_6522
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Montant field\_6523
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Inscription field\_6524
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 574. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   Type de justificatif field\_6526
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3314
    
    Reçu
    
    3315
    
    Facture
    
    3316
    
    Ticket
    
    3317
    
    Sans justificatif
    
    3318
    
    Autre
    
*   Pièce justificative field\_6527
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/694/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6518

field\_6519

field\_6520

field\_6521

field\_6522

field\_6523

field\_6524

field\_6526

field\_6527

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/694/?user_field_names=true" \
    --data '{
        "Nom": "string",
        "Date": "2020-01-01",
        "Type": 1,
        "Catégorie": 1,
        "Description": "string",
        "Montant": 0,
        "Inscription": [
            1
        ],
        "Type de justificatif": 1,
        "Pièce justificative": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ]
    }'

Example de réponse





field\_6518

field\_6519

field\_6520

field\_6521

field\_6522

field\_6523

field\_6524

field\_6526

field\_6527

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "Date": "2020-01-01",
        "Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Catégorie": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Description": "string",
        "Montant": 0,
        "Inscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Type de justificatif": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Pièce justificative": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table Mouvements de caisse.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Nom field\_6518
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Date field\_6519
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Type field\_6520
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3306
    
    Entrée
    
    3307
    
    Sortie
    
*   Catégorie field\_6521
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3308
    
    Inscription
    
    3309
    
    Don
    
    3310
    
    Matériel
    
    3311
    
    Transport
    
    3312
    
    Nourriture
    
    3313
    
    Divers
    
    3353
    
    Sacrement
    
*   Description field\_6522
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Montant field\_6523
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Inscription field\_6524
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 574. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   Type de justificatif field\_6526
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3314
    
    Reçu
    
    3315
    
    Facture
    
    3316
    
    Ticket
    
    3317
    
    Sans justificatif
    
    3318
    
    Autre
    
*   Pièce justificative field\_6527
    
    optionnel
    
    `array`
    
    Accepte un tableau d'objet contenant au moins le nom du fichier utilisateur. Vous pouvez également fournir une chaine de charactères contenant les noms des fichiers séparés par des virgules ou bien un tableau de nom de fichiers. Vous pouvez utiliser l'API « Envoi de fichier » pour envoyer des fichiers. La réponse à ces appels peut-être fournie directement en tant qu'objet ici. Les différentes API sont listées dans la barre latérale gauche.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6518

field\_6519

field\_6520

field\_6521

field\_6522

field\_6523

field\_6524

field\_6526

field\_6527

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row_id}/?user_field_names=true" \
    --data '{
        "Nom": "string",
        "Date": "2020-01-01",
        "Type": 1,
        "Catégorie": 1,
        "Description": "string",
        "Montant": 0,
        "Inscription": [
            1
        ],
        "Type de justificatif": 1,
        "Pièce justificative": [
            {
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png"
            }
        ]
    }'

Example de réponse





field\_6518

field\_6519

field\_6520

field\_6521

field\_6522

field\_6523

field\_6524

field\_6526

field\_6527

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "Date": "2020-01-01",
        "Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Catégorie": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Description": "string",
        "Montant": 0,
        "Inscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Type de justificatif": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Pièce justificative": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _Mouvements de caisse_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row_id}/move/"

Example de réponse





field\_6518

field\_6519

field\_6520

field\_6521

field\_6522

field\_6523

field\_6524

field\_6526

field\_6527

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Nom": "string",
        "Date": "2020-01-01",
        "Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Catégorie": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Description": "string",
        "Montant": 0,
        "Inscription": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "Type de justificatif": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Pièce justificative": [
            {
                "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "thumbnails": {
                    "tiny": {
                        "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 21,
                        "height": 21
                    },
                    "small": {
                        "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                        "width": 48,
                        "height": 48
                    }
                },
                "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "size": 229940,
                "mime_type": "image/png",
                "is_image": true,
                "image_width": 1280,
                "image_height": 585,
                "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*Mouvements de caisse\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/694/{row_id}/"

Table SystemActivityLog
-----------------------

L'identifiant de cette table est : `695`

### Champs

Chaque ligne dans la table « SystemActivityLog » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6528

Date

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date/heure au format ISO.

field\_6529

UserID

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6530

EntityType

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3319

Catechumene

3320

Parent

3321

Inscription

3322

Caisse

3323

Note

3324

ExtraitBapteme

3325

MagicLink

3326

Classe

field\_6532

EntityID

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6533

OperationType

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3327

Create

3328

Update

3329

Delete

field\_6534

EntitySnapshot

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6535

Changes

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6536

IPAddress

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6537

UserAgent

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6538

Status

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3330

Active

3331

Cancelled

3332

Restored

field\_6539

CancelledBy

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6541

CancellationTime

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date/heure au format ISO.

field\_6542

RelatedOperationID

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

### Lister les champs

Afin de lister les champs de la table SystemActivityLog une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/695/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/695/"

Example de réponse





    [
        {
            "id": 6528,
            "table_id": 695,
            "name": "Date",
            "order": 0,
            "type": "date",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6529,
            "table_id": 695,
            "name": "UserID",
            "order": 1,
            "type": "link_row",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6530,
            "table_id": 695,
            "name": "EntityType",
            "order": 2,
            "type": "single_select",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _SystemActivityLog_ une requête de type `GET` doit être envoyée au point d'accès de la table _SystemActivityLog_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/695/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/695/?user_field_names=true"

Example de réponse





field\_6528

field\_6529

field\_6530

field\_6532

field\_6533

field\_6534

field\_6535

field\_6536

field\_6537

field\_6538

field\_6539

field\_6541

field\_6542

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/695/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Date": "2020-01-01T12:00:00Z",
                "UserID": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "EntityType": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "EntityID": "string",
                "OperationType": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "EntitySnapshot": "string",
                "Changes": "string",
                "IPAddress": "string",
                "UserAgent": "string",
                "Status": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "CancelledBy": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "CancellationTime": "2020-01-01T12:00:00Z",
                "RelatedOperationID": 0
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table SystemActivityLog.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row_id}/?user_field_names=true"

Example de réponse





field\_6528

field\_6529

field\_6530

field\_6532

field\_6533

field\_6534

field\_6535

field\_6536

field\_6537

field\_6538

field\_6539

field\_6541

field\_6542

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Date": "2020-01-01T12:00:00Z",
        "UserID": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "EntityType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntityID": "string",
        "OperationType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntitySnapshot": "string",
        "Changes": "string",
        "IPAddress": "string",
        "UserAgent": "string",
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "CancellationTime": "2020-01-01T12:00:00Z",
        "RelatedOperationID": 0
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table SystemActivityLog.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Date field\_6528
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   UserID field\_6529
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   EntityType field\_6530
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3319
    
    Catechumene
    
    3320
    
    Parent
    
    3321
    
    Inscription
    
    3322
    
    Caisse
    
    3323
    
    Note
    
    3324
    
    ExtraitBapteme
    
    3325
    
    MagicLink
    
    3326
    
    Classe
    
*   EntityID field\_6532
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   OperationType field\_6533
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3327
    
    Create
    
    3328
    
    Update
    
    3329
    
    Delete
    
*   EntitySnapshot field\_6534
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Changes field\_6535
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   IPAddress field\_6536
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   UserAgent field\_6537
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Status field\_6538
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3330
    
    Active
    
    3331
    
    Cancelled
    
    3332
    
    Restored
    
*   CancelledBy field\_6539
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   CancellationTime field\_6541
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   RelatedOperationID field\_6542
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/695/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6528

field\_6529

field\_6530

field\_6532

field\_6533

field\_6534

field\_6535

field\_6536

field\_6537

field\_6538

field\_6539

field\_6541

field\_6542

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/695/?user_field_names=true" \
    --data '{
        "Date": "2020-01-01T12:00:00Z",
        "UserID": [
            1
        ],
        "EntityType": 1,
        "EntityID": "string",
        "OperationType": 1,
        "EntitySnapshot": "string",
        "Changes": "string",
        "IPAddress": "string",
        "UserAgent": "string",
        "Status": 1,
        "CancelledBy": [
            1
        ],
        "CancellationTime": "2020-01-01T12:00:00Z",
        "RelatedOperationID": 0
    }'

Example de réponse





field\_6528

field\_6529

field\_6530

field\_6532

field\_6533

field\_6534

field\_6535

field\_6536

field\_6537

field\_6538

field\_6539

field\_6541

field\_6542

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Date": "2020-01-01T12:00:00Z",
        "UserID": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "EntityType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntityID": "string",
        "OperationType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntitySnapshot": "string",
        "Changes": "string",
        "IPAddress": "string",
        "UserAgent": "string",
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "CancellationTime": "2020-01-01T12:00:00Z",
        "RelatedOperationID": 0
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table SystemActivityLog.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Date field\_6528
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   UserID field\_6529
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   EntityType field\_6530
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3319
    
    Catechumene
    
    3320
    
    Parent
    
    3321
    
    Inscription
    
    3322
    
    Caisse
    
    3323
    
    Note
    
    3324
    
    ExtraitBapteme
    
    3325
    
    MagicLink
    
    3326
    
    Classe
    
*   EntityID field\_6532
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   OperationType field\_6533
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3327
    
    Create
    
    3328
    
    Update
    
    3329
    
    Delete
    
*   EntitySnapshot field\_6534
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Changes field\_6535
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   IPAddress field\_6536
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   UserAgent field\_6537
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Status field\_6538
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3330
    
    Active
    
    3331
    
    Cancelled
    
    3332
    
    Restored
    
*   CancelledBy field\_6539
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   CancellationTime field\_6541
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   RelatedOperationID field\_6542
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6528

field\_6529

field\_6530

field\_6532

field\_6533

field\_6534

field\_6535

field\_6536

field\_6537

field\_6538

field\_6539

field\_6541

field\_6542

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row_id}/?user_field_names=true" \
    --data '{
        "Date": "2020-01-01T12:00:00Z",
        "UserID": [
            1
        ],
        "EntityType": 1,
        "EntityID": "string",
        "OperationType": 1,
        "EntitySnapshot": "string",
        "Changes": "string",
        "IPAddress": "string",
        "UserAgent": "string",
        "Status": 1,
        "CancelledBy": [
            1
        ],
        "CancellationTime": "2020-01-01T12:00:00Z",
        "RelatedOperationID": 0
    }'

Example de réponse





field\_6528

field\_6529

field\_6530

field\_6532

field\_6533

field\_6534

field\_6535

field\_6536

field\_6537

field\_6538

field\_6539

field\_6541

field\_6542

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Date": "2020-01-01T12:00:00Z",
        "UserID": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "EntityType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntityID": "string",
        "OperationType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntitySnapshot": "string",
        "Changes": "string",
        "IPAddress": "string",
        "UserAgent": "string",
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "CancellationTime": "2020-01-01T12:00:00Z",
        "RelatedOperationID": 0
    }

### Déplacer une ligne

Déplace une ligne existante de la table _SystemActivityLog_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row_id}/move/"

Example de réponse





field\_6528

field\_6529

field\_6530

field\_6532

field\_6533

field\_6534

field\_6535

field\_6536

field\_6537

field\_6538

field\_6539

field\_6541

field\_6542

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Date": "2020-01-01T12:00:00Z",
        "UserID": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "EntityType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntityID": "string",
        "OperationType": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "EntitySnapshot": "string",
        "Changes": "string",
        "IPAddress": "string",
        "UserAgent": "string",
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "CancelledBy": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "CancellationTime": "2020-01-01T12:00:00Z",
        "RelatedOperationID": 0
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*SystemActivityLog\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/695/{row_id}/"

Table SMS\_Messages
-------------------

L'identifiant de cette table est : `696`

### Champs

Chaque ligne dans la table « SMS\_Messages » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6543

Message\_ID

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6544

Phone

`string`

`equal``not_equal``contains``contains_not``length_is_lower_than``empty``not_empty`

Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .

field\_6545

Text

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6546

Sender\_Name

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6547

SMS\_Type

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3333

normal

3334

flash

field\_6548

Status\_ID

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6549

Status\_Description

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6550

SMS\_Count

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6551

Sent\_At

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date au format ISO.

field\_6552

Scheduled\_At

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date/heure au format ISO.

field\_6553

User

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6566

SMS\_Campaigns

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 697. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

### Lister les champs

Afin de lister les champs de la table SMS\_Messages une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/696/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/696/"

Example de réponse





    [
        {
            "id": 6543,
            "table_id": 696,
            "name": "Message_ID",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6544,
            "table_id": 696,
            "name": "Phone",
            "order": 1,
            "type": "phone_number",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6545,
            "table_id": 696,
            "name": "Text",
            "order": 2,
            "type": "long_text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _SMS\_Messages_ une requête de type `GET` doit être envoyée au point d'accès de la table _SMS\_Messages_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/696/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/696/?user_field_names=true"

Example de réponse





field\_6543

field\_6544

field\_6545

field\_6546

field\_6547

field\_6548

field\_6549

field\_6550

field\_6551

field\_6552

field\_6553

field\_6566

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/696/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Message_ID": "string",
                "Phone": "+1-541-754-3010",
                "Text": "string",
                "Sender_Name": "string",
                "SMS_Type": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Status_ID": 0,
                "Status_Description": "string",
                "SMS_Count": 0,
                "Sent_At": "2020-01-01",
                "Scheduled_At": "2020-01-01T12:00:00Z",
                "User": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "SMS_Campaigns": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table SMS\_Messages.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row_id}/?user_field_names=true"

Example de réponse





field\_6543

field\_6544

field\_6545

field\_6546

field\_6547

field\_6548

field\_6549

field\_6550

field\_6551

field\_6552

field\_6553

field\_6566

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Message_ID": "string",
        "Phone": "+1-541-754-3010",
        "Text": "string",
        "Sender_Name": "string",
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Status_ID": 0,
        "Status_Description": "string",
        "SMS_Count": 0,
        "Sent_At": "2020-01-01",
        "Scheduled_At": "2020-01-01T12:00:00Z",
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table SMS\_Messages.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Message\_ID field\_6543
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Phone field\_6544
    
    optionnel
    
    `string`
    
    Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .
    
*   Text field\_6545
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Sender\_Name field\_6546
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SMS\_Type field\_6547
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3333
    
    normal
    
    3334
    
    flash
    
*   Status\_ID field\_6548
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Status\_Description field\_6549
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SMS\_Count field\_6550
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Sent\_At field\_6551
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Scheduled\_At field\_6552
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   User field\_6553
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Campaigns field\_6566
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 697. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/696/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6543

field\_6544

field\_6545

field\_6546

field\_6547

field\_6548

field\_6549

field\_6550

field\_6551

field\_6552

field\_6553

field\_6566

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/696/?user_field_names=true" \
    --data '{
        "Message_ID": "string",
        "Phone": "+1-541-754-3010",
        "Text": "string",
        "Sender_Name": "string",
        "SMS_Type": 1,
        "Status_ID": 0,
        "Status_Description": "string",
        "SMS_Count": 0,
        "Sent_At": "2020-01-01",
        "Scheduled_At": "2020-01-01T12:00:00Z",
        "User": [
            1
        ],
        "SMS_Campaigns": [
            1
        ]
    }'

Example de réponse





field\_6543

field\_6544

field\_6545

field\_6546

field\_6547

field\_6548

field\_6549

field\_6550

field\_6551

field\_6552

field\_6553

field\_6566

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Message_ID": "string",
        "Phone": "+1-541-754-3010",
        "Text": "string",
        "Sender_Name": "string",
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Status_ID": 0,
        "Status_Description": "string",
        "SMS_Count": 0,
        "Sent_At": "2020-01-01",
        "Scheduled_At": "2020-01-01T12:00:00Z",
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table SMS\_Messages.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Message\_ID field\_6543
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Phone field\_6544
    
    optionnel
    
    `string`
    
    Accepte un numéro de téléphone d'une longueur maximum de 100 caractères qui doivent être des chiffres, des espaces ou les caractères suivants : Nx,.\_+\*()#=;/- .
    
*   Text field\_6545
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Sender\_Name field\_6546
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SMS\_Type field\_6547
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3333
    
    normal
    
    3334
    
    flash
    
*   Status\_ID field\_6548
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Status\_Description field\_6549
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   SMS\_Count field\_6550
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Sent\_At field\_6551
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Scheduled\_At field\_6552
    
    optionnel
    
    `date`
    
    Accepte une date/heure au format ISO.
    
*   User field\_6553
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Campaigns field\_6566
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 697. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6543

field\_6544

field\_6545

field\_6546

field\_6547

field\_6548

field\_6549

field\_6550

field\_6551

field\_6552

field\_6553

field\_6566

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row_id}/?user_field_names=true" \
    --data '{
        "Message_ID": "string",
        "Phone": "+1-541-754-3010",
        "Text": "string",
        "Sender_Name": "string",
        "SMS_Type": 1,
        "Status_ID": 0,
        "Status_Description": "string",
        "SMS_Count": 0,
        "Sent_At": "2020-01-01",
        "Scheduled_At": "2020-01-01T12:00:00Z",
        "User": [
            1
        ],
        "SMS_Campaigns": [
            1
        ]
    }'

Example de réponse





field\_6543

field\_6544

field\_6545

field\_6546

field\_6547

field\_6548

field\_6549

field\_6550

field\_6551

field\_6552

field\_6553

field\_6566

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Message_ID": "string",
        "Phone": "+1-541-754-3010",
        "Text": "string",
        "Sender_Name": "string",
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Status_ID": 0,
        "Status_Description": "string",
        "SMS_Count": 0,
        "Sent_At": "2020-01-01",
        "Scheduled_At": "2020-01-01T12:00:00Z",
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _SMS\_Messages_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row_id}/move/"

Example de réponse





field\_6543

field\_6544

field\_6545

field\_6546

field\_6547

field\_6548

field\_6549

field\_6550

field\_6551

field\_6552

field\_6553

field\_6566

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Message_ID": "string",
        "Phone": "+1-541-754-3010",
        "Text": "string",
        "Sender_Name": "string",
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Status_ID": 0,
        "Status_Description": "string",
        "SMS_Count": 0,
        "Sent_At": "2020-01-01",
        "Scheduled_At": "2020-01-01T12:00:00Z",
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Campaigns": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*SMS\_Messages\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/696/{row_id}/"

Table SMS\_Campaigns
--------------------

L'identifiant de cette table est : `697`

### Champs

Chaque ligne dans la table « SMS\_Campaigns » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6555

Campaign\_Name

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6556

Campaign\_ID

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6557

SMS\_Type

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3335

normal

3336

flash

field\_6558

Sender\_Name

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6559

Created\_At

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date au format ISO.

field\_6560

Scheduled\_At

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date au format ISO.

field\_6561

Total\_Recipients

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6562

Total\_SMS\_Count

`number`

`equal``not_equal``contains``contains_not``higher_than``higher_than_or_equal``lower_than``lower_than_or_equal``is_even_and_whole``empty``not_empty`

Accepte un entier positive.

field\_6563

Status

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3337

Draft

3338

Sent

3339

Scheduled

3340

Failed

field\_6564

User

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

field\_6567

SMS\_Messages

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 696. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

### Lister les champs

Afin de lister les champs de la table SMS\_Campaigns une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/697/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/697/"

Example de réponse





    [
        {
            "id": 6555,
            "table_id": 697,
            "name": "Campaign_Name",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6556,
            "table_id": 697,
            "name": "Campaign_ID",
            "order": 1,
            "type": "number",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6557,
            "table_id": 697,
            "name": "SMS_Type",
            "order": 2,
            "type": "single_select",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _SMS\_Campaigns_ une requête de type `GET` doit être envoyée au point d'accès de la table _SMS\_Campaigns_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/697/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/697/?user_field_names=true"

Example de réponse





field\_6555

field\_6556

field\_6557

field\_6558

field\_6559

field\_6560

field\_6561

field\_6562

field\_6563

field\_6564

field\_6567

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/697/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Campaign_Name": "string",
                "Campaign_ID": 0,
                "SMS_Type": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Sender_Name": "string",
                "Created_At": "2020-01-01",
                "Scheduled_At": "2020-01-01",
                "Total_Recipients": 0,
                "Total_SMS_Count": 0,
                "Status": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "User": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ],
                "SMS_Messages": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table SMS\_Campaigns.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row_id}/?user_field_names=true"

Example de réponse





field\_6555

field\_6556

field\_6557

field\_6558

field\_6559

field\_6560

field\_6561

field\_6562

field\_6563

field\_6564

field\_6567

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Campaign_Name": "string",
        "Campaign_ID": 0,
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Sender_Name": "string",
        "Created_At": "2020-01-01",
        "Scheduled_At": "2020-01-01",
        "Total_Recipients": 0,
        "Total_SMS_Count": 0,
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table SMS\_Campaigns.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Campaign\_Name field\_6555
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Campaign\_ID field\_6556
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   SMS\_Type field\_6557
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3335
    
    normal
    
    3336
    
    flash
    
*   Sender\_Name field\_6558
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Created\_At field\_6559
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Scheduled\_At field\_6560
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Total\_Recipients field\_6561
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Total\_SMS\_Count field\_6562
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Status field\_6563
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3337
    
    Draft
    
    3338
    
    Sent
    
    3339
    
    Scheduled
    
    3340
    
    Failed
    
*   User field\_6564
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Messages field\_6567
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 696. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/697/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6555

field\_6556

field\_6557

field\_6558

field\_6559

field\_6560

field\_6561

field\_6562

field\_6563

field\_6564

field\_6567

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/697/?user_field_names=true" \
    --data '{
        "Campaign_Name": "string",
        "Campaign_ID": 0,
        "SMS_Type": 1,
        "Sender_Name": "string",
        "Created_At": "2020-01-01",
        "Scheduled_At": "2020-01-01",
        "Total_Recipients": 0,
        "Total_SMS_Count": 0,
        "Status": 1,
        "User": [
            1
        ],
        "SMS_Messages": [
            1
        ]
    }'

Example de réponse





field\_6555

field\_6556

field\_6557

field\_6558

field\_6559

field\_6560

field\_6561

field\_6562

field\_6563

field\_6564

field\_6567

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Campaign_Name": "string",
        "Campaign_ID": 0,
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Sender_Name": "string",
        "Created_At": "2020-01-01",
        "Scheduled_At": "2020-01-01",
        "Total_Recipients": 0,
        "Total_SMS_Count": 0,
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table SMS\_Campaigns.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Campaign\_Name field\_6555
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Campaign\_ID field\_6556
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   SMS\_Type field\_6557
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3335
    
    normal
    
    3336
    
    flash
    
*   Sender\_Name field\_6558
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Created\_At field\_6559
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Scheduled\_At field\_6560
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Total\_Recipients field\_6561
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Total\_SMS\_Count field\_6562
    
    optionnel
    
    `number`
    
    Accepte un entier positive.
    
*   Status field\_6563
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3337
    
    Draft
    
    3338
    
    Sent
    
    3339
    
    Scheduled
    
    3340
    
    Failed
    
*   User field\_6564
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    
*   SMS\_Messages field\_6567
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 696. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6555

field\_6556

field\_6557

field\_6558

field\_6559

field\_6560

field\_6561

field\_6562

field\_6563

field\_6564

field\_6567

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row_id}/?user_field_names=true" \
    --data '{
        "Campaign_Name": "string",
        "Campaign_ID": 0,
        "SMS_Type": 1,
        "Sender_Name": "string",
        "Created_At": "2020-01-01",
        "Scheduled_At": "2020-01-01",
        "Total_Recipients": 0,
        "Total_SMS_Count": 0,
        "Status": 1,
        "User": [
            1
        ],
        "SMS_Messages": [
            1
        ]
    }'

Example de réponse





field\_6555

field\_6556

field\_6557

field\_6558

field\_6559

field\_6560

field\_6561

field\_6562

field\_6563

field\_6564

field\_6567

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Campaign_Name": "string",
        "Campaign_ID": 0,
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Sender_Name": "string",
        "Created_At": "2020-01-01",
        "Scheduled_At": "2020-01-01",
        "Total_Recipients": 0,
        "Total_SMS_Count": 0,
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _SMS\_Campaigns_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row_id}/move/"

Example de réponse





field\_6555

field\_6556

field\_6557

field\_6558

field\_6559

field\_6560

field\_6561

field\_6562

field\_6563

field\_6564

field\_6567

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Campaign_Name": "string",
        "Campaign_ID": 0,
        "SMS_Type": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Sender_Name": "string",
        "Created_At": "2020-01-01",
        "Scheduled_At": "2020-01-01",
        "Total_Recipients": 0,
        "Total_SMS_Count": 0,
        "Status": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ],
        "SMS_Messages": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*SMS\_Campaigns\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/697/{row_id}/"

Table SMS\_Templates
--------------------

L'identifiant de cette table est : `698`

### Champs

Chaque ligne dans la table « SMS\_Templates » contient les champs décrits ci-dessous.

ID

Nom

Type

Filtres compatibles

field\_6568

Template\_Name

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte une seule ligne de texte.

field\_6569

Template\_Text

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6570

Category

`integer or string`

`contains``contains_not``contains_word``doesnt_contain_word``single_select_equal``single_select_not_equal``single_select_is_any_of``single_select_is_none_of``empty``not_empty`

Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  

3341

Magic Link

3342

Notification

3343

Reminder

3344

General

field\_6571

Variables

`string`

`equal``not_equal``contains``contains_not``contains_word``doesnt_contain_word``length_is_lower_than``empty``not_empty`

Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.

field\_6572

Created\_At

`date`

`date_is``date_is_not``date_is_before``date_is_on_or_before``date_is_after``date_is_on_or_after``date_is_within``date_equal``date_not_equal``date_equals_today``date_before_today``date_after_today``date_within_days``date_within_weeks``date_within_months``date_equals_days_ago``date_equals_months_ago``date_equals_years_ago``date_equals_week``date_equals_month``date_equals_year``date_equals_day_of_month``date_before``date_before_or_equal``date_after``date_after_or_equal``date_after_days_ago``contains``contains_not``empty``not_empty`

Accepte une date au format ISO.

field\_6573

Is\_Active

`boolean`

`boolean``empty``not_empty`

Accepte une valeur booléenne.

field\_6574

User

`array`

`link_row_has``link_row_has_not``link_row_contains``link_row_not_contains``empty``not_empty`

Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.

### Lister les champs

Afin de lister les champs de la table SMS\_Templates une requête de type doit être envoyé auprès du point d'accès des champs de celle-ci. Le jeton d'authentification doit avoir les droits de création, modification et suppression afin de pouvoir lister les champs de la table.

#### Propriétés des champs de la réponse

*   id
    
    `integer`
    
    Clé primaire du champ. Permet de générer le nom de la colonne en base de données en ajoutant le prefix `field_`.
    
*   name
    
    `string`
    
    Nom du champ.
    
*   table\_id
    
    `integer`
    
    ID de table associée.
    
*   order
    
    `integer`
    
    Ordre du champ dans la table. 0 est pour le premier champ.
    
*   primary
    
    `boolean`
    
    Indique si le champ est une clé primaire. Si la valeur est `true` le champ ne peut être effacé et ses valeurs doivent représenter la ligne entière.
    
*   type
    
    `string`
    
    Type défini pour ce champ.
    
*   read\_only
    
    `boolean`
    
    Indique si le champ est un champ de lecture uniquement. Si oui, il n'est pas possible de mettre à jour la valeur de la cellule.
    
*   description
    
    `string`
    
    Description du champ
    

Certaines propriétés ne sont pas décrites ici car elles sont spécifiques au type de champ concerné.





GET

https://sdbaserow.3xperts.tech/api/database/fields/table/698/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/fields/table/698/"

Example de réponse





    [
        {
            "id": 6568,
            "table_id": 698,
            "name": "Template_Name",
            "order": 0,
            "type": "text",
            "primary": true,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6569,
            "table_id": 698,
            "name": "Template_Text",
            "order": 1,
            "type": "long_text",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        },
        {
            "id": 6570,
            "table_id": 698,
            "name": "Category",
            "order": 2,
            "type": "single_select",
            "primary": false,
            "read_only": false,
            "description": "A sample description"
        }
    ]

### Lister les lignes

Afin de lister les lignes de la table _SMS\_Templates_ une requête de type `GET` doit être envoyée au point d'accès de la table _SMS\_Templates_. La réponse est paginée et par défault la première page est retournée. La page désirée peut-être récupérée en définissant les paramètres de requête `page` et `size`.

#### Paramètres de requête

*   page
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 1
    
    Permet de choisir la page.
    
*   size
    
    optionnel
    
    `integer`
    
    Valeur par défaut : 100
    
    Permet de définir le nombre de ligne par page.
    
*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand la valeur fournie pour le paramètre GET `user_field_names` est une des valeur suivante : `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms des champs du résultat seront ceux définis par l'utilisateur.
    
    Si le paramêtre `user_field_names` n'est pas défini ou n'est pas l'une des valeurs citées plus haut, alors les noms des champs seront `field_` suivis par l'identifiant du champ. Par exemple `field_1` fait référence au champ avec l'identifiant `1`.
    
    De plus, quand `user_field_names` est défini, vous devez également fournir les noms définis par l'utilisateur pour les paramètres `order_by`, `include` et `exclude`.
    
*   search
    
    optionnel
    
    `string`
    
    Valeur par défaut : ''
    
    Quand ce paramètre est défini, seules les lignes qui satisfont la recherche seront retournées.
    
*   order\_by
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'id'
    
    Ce paramètre permet d'ordonner les lignes du résultat à l'aide d'une liste de champs séparés par une virgule. Par défaut ou s'il est préfixé par un `+` un champ est ordonné par ordre croissant (A-Z), en le préfixant par un `-` il sera ordonné par ordre décroissant (Z-A).
    
    #### Avec `user_field_names` :
    
    `order_by` doit être une liste de noms définis par l'utilisateur des champs sur lesquels s'appuient l'ordre séparés par des virgules. Par exemple si vous fournissez la valeur suivante `order_by=Mon champ,-Mon champ 2` les lignes seront ordonnées par le champ appelé `Mon champ` par ordre croissant. Si certaines lignes ont la même valeur pour `Mon champ` ce sous ensemble sera ordonné par la valeur du champ `Mon champ 2` par ordre décroissant.
    
    Assurez vous que les champs qui commencent par un `+` ou un `-` soit explicitement préfixés par un autre `+` ou `-`. Ex : `+-Nom`.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `order_by` doit être une liste de `field_` suivi par l'identifiant du champ à ordonner, séparés par des virgules. Par exemple si vous fournissez la valeur suivante pour ce paramètre `order_by=field_1,-field_2` les lignes seront ordonnées par le champ `field_1` par ordre croissant. Si certaines lignes ont la même valeur pour ce champ, ce sous ensemble sera ordonné par la valeur du champ `field_2` par ordre décroissant.
    
*   filters
    
    optionnel
    
    `JSON`
    
    Les lignes peuvent être filtrées en utilisant les mêmes filtres que ceux disponibles pour les vues. Ce paramètre accepte une chaîne sérialisée en JSON contenant l'arbre de filtre à appliquer pour cette vue. L'arbre de filtre est une structure imbriquée contenant les filtres qui doivent être appliqués.
    
    #### Avec `user_field_names` :
    
    Un exemple d'arbre de filtre valide est le suivant : `{"filter_type": "AND", "filters": [{"field": "Name", "type": "equal", "value": "test"}]}`
    
    #### Sans `user_field_names` :
    
    Par exemple, si vous fournissez le paramètre GET suivant : `{"filter_type": "AND", "filters": [{"field": 1, "type": "equal", "value": "test"}]}`
    
    Veuillez noter que si ce paramètre est fourni, tous les autres `filter__{field}__{filter}` seront ignorés, ainsi que le paramètre `filter_type`.
    
    Ouvrir le générateur de filtres
    
*   filter\_\_{field}\_\_{filter}
    
    optionnel
    
    `string`
    
    Ce paramètre permet de filtrer les lignes avec les même filtres que ceux disponibles pour les vues. Plusieurs filtres peuvent être définis simultanéement s'il suivent le même format. La variable `field` permet d'indiquer le champ à filtrer, tandis que `filter` permet de choiser le type de filtre.
    
    #### Avec l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__Nom__equal=test`, seule les lignes pour lesquelles la valeur du champ nommé `Nom` est égale à _test_ seront retournées. Cette méthode est rétro-compatible et test également en utilisant `field_id` si le test échoue pour le champ `Nom`.
    
    #### Sans l'option `user_field_names` :
    
    Par exemple si vous utilisez la valeur suivante : `filter__field_1__equal=test`, seule les lignes pour lesquelles la valeur du champ `field_1` est égale à _test_ seront retournées.
    
    Veuillez notez que si le paramètre `filters` est fournie, ce paramètre sera ignoré.
    
    Une liste des filtres disponibles peut être consultée ici.
    
*   filter\_type
    
    optionnel
    
    `string`
    
    Valeur par défaut : 'AND'
    
    *   `AND` : indique que les lignes doivent satisfaire tous les filtres définis.
    *   `OR` : indique que les lignes doivent satisfaire au moins l'un des filtres définis pour être retournées.
    
    Cela fonctionne uniquement quand au moins 2 filtres sont définis.
    
*   include
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés. Vous pouvez définir le sous ensemble des champs qui seront dans les résultats en fournissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `include` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez conserver, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante `include=Mon champ,-Mon champ 2` alors seul ces champs seront retournés dans les résultats (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `include` doit être une liste de `field_` suivis par l'identifiant d'un champ à inclure dans le résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante `include=field_1,field_2` alors les champs d'identifiant `1` et `2` seront les champs présents dans le résultat (sauf si vous les avez explicitement exclus avec le paramètre suivant).
    
*   exclude
    
    optionnel
    
    `string`
    
    Par défaut, tous les champs de la table sont retournés dans les résultats. Vous pouvez choisir un sous ensemble de champs qui seront exclus des résultats en définissant une valeur pour ce paramètre.
    
    #### Avec `user_field_names` :
    
    `exclude` doit être une liste des noms définis par l'utilisateur des champs que vous souhaitez exclure, séparés par une virgule. Par exemple, si vous fournissez la valeur suivante : `exclude=Mon champ,-Mon champ 2` alors ces deux champs seront exclus des résultats.
    
    Le nom des champs contenant des virgules doit être entouré par des guillemets : `"Nom ,"`. Si le nom des champs contient des guillemets, ceux-ci doivent être protégés en utilisant le caractère `\`. Ex : `Nom \"`.
    
    #### Sans `user_field_names` :
    
    `exclude` doit être une liste de `field_` suivis par l'identifiant d'un champ à exclure du résultat, séparé par des virgules. Par exemple, si vous fournissez la valeur suivante : `exclude=field_1,field_2` alors les champs avec l'identifiant `1` et `2` seront exclus.
    
*   view\_id
    
    optionnel
    
    `integer`
    
    Par défaut, aucun des filtres et tris autres que ceux définis dans les paramètres de la requête ne sont appliqués. Vous pouvez définir les filtres et les tris d'une vue en fournissant son `id` dans le paramètre GET `view_id`. Par exemple, si vous fournissez le paramètre GET suivant `view_id=1`, les filtres et les tris définis dans la vue avec l'id `1` seront appliqués. Vous pouvez trouver le `view_id` dans le menu contextuel d'une vue donnée. Il s'agit du nombre entre parenthèses derrière le nom de la vue.
    
    #### Avec `filter__{field}__{filter}`
    
    Le filtre fourni dans le paramètre de la requête et les filtres définis dans la vue seront appliqués.
    
    #### Avec `order_by`
    
    Si `order_by` est fourni, le tri défini dans la vue sera ignoré.
    
*   {link\_row\_field}\_\_join
    
    optionnel
    
    `string`
    
    Permet de consulter les valeurs des champs d'une table liée par l'intermédiaire des champs de lien de la table courante. Le nom du paramètre doit être le nom d'un champ de lien existant, suivi de `__join`. La valeur doit être une liste de noms de champs pour lesquels vous souhaiter inclure les valeurs. Vous pouvez fournir un ou plusieurs champs cibles. Il n'est pas possible de rechercher la valeur d'un champ de lien dans la table liée.
    
    #### Avec `user_field_names` :
    
    `join` doit être une liste de noms de champs séparés par des virgules à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `LinkRowField__join=MyField,MyField2`, les valeurs de `MyField` et `My Field2` dans la table liée par `LinkRowField` seront incluses dans la réponse.
    
    #### Sans `user_field_names` :
    
    `join` doit être une liste de `field_` séparés par des virgules, suivi de l'identifiant du champ à inclure dans les résultats. Par exemple, si vous fournissez le paramètre GET suivant `field_1__join=field_2,field_3` alors les valeurs de `field_2` et `field_3` dans la table liée par `field_1` seront incluses dans la réponse.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/698/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/698/?user_field_names=true"

Example de réponse





field\_6568

field\_6569

field\_6570

field\_6571

field\_6572

field\_6573

field\_6574

    {
        "count": 1024,
        "next": "https://sdbaserow.3xperts.tech/api/database/rows/table/698/?page=2",
        "previous": null,
        "results": [
            {
                "id": 0,
                "order": "1.00000000000000000000",
                "Template_Name": "string",
                "Template_Text": "string",
                "Category": {
                    "id": 1,
                    "value": "Option",
                    "color": "light-blue"
                },
                "Variables": "string",
                "Created_At": "2020-01-01",
                "Is_Active": true,
                "User": [
                    {
                        "id": 0,
                        "value": "string"
                    }
                ]
            }
        ]
    }

### Lire une ligne

Retourne une ligne de la table SMS\_Templates.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne demandée.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    





GET

https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X GET \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row_id}/?user_field_names=true"

Example de réponse





field\_6568

field\_6569

field\_6570

field\_6571

field\_6572

field\_6573

field\_6574

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Template_Name": "string",
        "Template_Text": "string",
        "Category": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Variables": "string",
        "Created_At": "2020-01-01",
        "Is_Active": true,
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Créer une ligne

batch mode

Créé une nouvelle ligne pour la table SMS\_Templates.

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before
    
    optionnel
    
    `integer`
    
    Si ce paramètre est fourni, la nouvelle ligne sera positionnée avant la ligne portant l'identifiant fourni.
    

#### Schéma du corps de la requête

*   Template\_Name field\_6568
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Template\_Text field\_6569
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Category field\_6570
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3341
    
    Magic Link
    
    3342
    
    Notification
    
    3343
    
    Reminder
    
    3344
    
    General
    
*   Variables field\_6571
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Created\_At field\_6572
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Is\_Active field\_6573
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   User field\_6574
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





POST

https://sdbaserow.3xperts.tech/api/database/rows/table/698/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6568

field\_6569

field\_6570

field\_6571

field\_6572

field\_6573

field\_6574

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/698/?user_field_names=true" \
    --data '{
        "Template_Name": "string",
        "Template_Text": "string",
        "Category": 1,
        "Variables": "string",
        "Created_At": "2020-01-01",
        "Is_Active": true,
        "User": [
            1
        ]
    }'

Example de réponse





field\_6568

field\_6569

field\_6570

field\_6571

field\_6572

field\_6573

field\_6574

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Template_Name": "string",
        "Template_Text": "string",
        "Category": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Variables": "string",
        "Created_At": "2020-01-01",
        "Is_Active": true,
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Modifier une ligne

batch mode

Modifie une ligne existante de la table SMS\_Templates.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à modifier.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    

#### Schéma du corps de la requête

*   Template\_Name field\_6568
    
    optionnel
    
    `string`
    
    Accepte une seule ligne de texte.
    
*   Template\_Text field\_6569
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Category field\_6570
    
    optionnel
    
    `integer or string`
    
    Accepte un nombre entier ou une valeur textuelle représentant l'identifiant de l'option de sélection choisie ou la valeur de l'option. Une valeur nulle signifie qu'aucune option n'est sélectionnée. Dans le cas d'une valeur textuelle, la première option correspondante est sélectionnée.  
    
    3341
    
    Magic Link
    
    3342
    
    Notification
    
    3343
    
    Reminder
    
    3344
    
    General
    
*   Variables field\_6571
    
    optionnel
    
    `string`
    
    Accepte le texte sur multi-lignes. Si le formatage de texte riche est activé, vous pouvez utiliser markdown pour formater le texte.
    
*   Created\_At field\_6572
    
    optionnel
    
    `date`
    
    Accepte une date au format ISO.
    
*   Is\_Active field\_6573
    
    optionnel
    
    `boolean`
    
    Accepte une valeur booléenne.
    
*   User field\_6574
    
    optionnel
    
    `array`
    
    Accepte un tableau contenant les identifiants ou les valeurs textuelles des champs principaux des lignes liées de la table 578. Tous les identifiants doivent être fournis à chaque fois que les relations sont mises à jour. Si un tableau vide est fourni, toutes les relations seront supprimées. Dans le cas d'une valeur textuelle au lieu d'un identifiant, une ligne avec la valeur correspondante pour son champ principal sera recherchée. Si plusieurs correspondances sont trouvées, la première dans l'ordre du tableau est sélectionnée. Vous pouvez également envoyer un chaine de caractères avec les noms séparés par des virgules, dans ce cas la chaine sera convertie en une liste de noms. Vous pouvez également envoyer un unique ID de ligne.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row\_id}/?user\_field\_names=true

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

field\_6568

field\_6569

field\_6570

field\_6571

field\_6572

field\_6573

field\_6574

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row_id}/?user_field_names=true" \
    --data '{
        "Template_Name": "string",
        "Template_Text": "string",
        "Category": 1,
        "Variables": "string",
        "Created_At": "2020-01-01",
        "Is_Active": true,
        "User": [
            1
        ]
    }'

Example de réponse





field\_6568

field\_6569

field\_6570

field\_6571

field\_6572

field\_6573

field\_6574

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Template_Name": "string",
        "Template_Text": "string",
        "Category": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Variables": "string",
        "Created_At": "2020-01-01",
        "Is_Active": true,
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Déplacer une ligne

Déplace une ligne existante de la table _SMS\_Templates_ avant une autre ligne. Si le paramètre `before_id` n'est pas fourni, la ligne est déplacée à la fin de la table.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    Identifiant unique de la ligne à déplacer.
    

#### Paramètres de requête

*   user\_field\_names
    
    optionnel
    
    `any`
    
    Quand valeur définie pour le paramètre GET `user_field_names` est l'une des suivantes `y`, `yes`, `true`, `t`, `on`, `1`, ou `""`, les noms de champs retournés par ce point d'accès seront les noms définis par l'utilisateur.
    
    Si le paramètre `user_field_names` n'est pas fourni, ou s'il ne correspond à aucune des valeurs ci-dessus, alors le nom des champs sera `field_` suivi par l'identifiant du champ. Par exemple `field_1` fait référence au champ dont l'identifiant est `1`.
    
*   before\_id
    
    optionnel
    
    `integer`
    
    Permet de définir l'identifiant de la ligne avant laquelle la ligne choisie doit être déplacée. Si aucune valeur n'est fournie, la ligne est déplacée à la fin de la table.
    





PATCH

https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row\_id}/move/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -X PATCH \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row_id}/move/"

Example de réponse





field\_6568

field\_6569

field\_6570

field\_6571

field\_6572

field\_6573

field\_6574

    {
        "id": 0,
        "order": "1.00000000000000000000",
        "Template_Name": "string",
        "Template_Text": "string",
        "Category": {
            "id": 1,
            "value": "Option",
            "color": "light-blue"
        },
        "Variables": "string",
        "Created_At": "2020-01-01",
        "Is_Active": true,
        "User": [
            {
                "id": 0,
                "value": "string"
            }
        ]
    }

### Supprimer une ligne

batch mode

Supprime une ligne de la table \*SMS\_Templates\*.

#### Paramètres d'URL

*   row\_id
    
    `integer`
    
    L'identifiant unique de la ligne à supprimer.
    





DELETE

https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row\_id}/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X DELETE \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech/api/database/rows/table/698/{row_id}/"

### Téléverser un fichier

Envoi un fichier sur Baserow en envoyant directement le contenu du fichier. Un section multipart `file` contenant le contenu du fichier est attendu dans la requête. La réponse peut ensuite être utilisée pour [associer un fichier à une ligne](https://sdbaserow.3xperts.tech/api/redoc/#tag/Database-table-rows/operation/update_database_table_row).

#### Schéma du corps de la requête

*   file
    
    `multipart`
    
    La section multipart `file` contenant le contenu du fichier.
    





POST

https://sdbaserow.3xperts.tech/api/user-files/upload-file/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \ \
    -F file=@photo.png
    "https://sdbaserow.3xperts.tech/api/user-files/upload-file/"

Example de réponse





    {
        "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
        "thumbnails": {
            "tiny": {
                "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "width": 21,
                "height": 21
            },
            "small": {
                "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "width": 48,
                "height": 48
            }
        },
        "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
        "size": 229940,
        "mime_type": "image/png",
        "is_image": true,
        "image_width": 1280,
        "image_height": 585,
        "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
    }

### Téléverser un fichier via une URL

Envoi un fichier sur Baserow en le téléchargeant depuis l'URL fournie. La réponse peut ensuite être utilisée pour [associer un fichier à une ligne](https://sdbaserow.3xperts.tech/api/redoc/#tag/Database-table-rows/operation/update_database_table_row).

#### Schéma du corps de la requête

*   url
    
    `string`
    
    Téléverse un fichier sur Baserow en le récupérant depuis l'URL fournie.
    





POST

https://sdbaserow.3xperts.tech/api/user-files/upload-via-url/

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

    curl \
    -X POST \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    -H "Content-Type: application/json" \
    "https://sdbaserow.3xperts.tech/api/user-files/upload-via-url/" \
    --data '{
        "url": "https://baserow.io/assets/photo.png"
    }'

Example de réponse





    {
        "url": "https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
        "thumbnails": {
            "tiny": {
                "url": "https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "width": 21,
                "height": 21
            },
            "small": {
                "url": "https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
                "width": 48,
                "height": 48
            }
        },
        "name": "VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png",
        "size": 229940,
        "mime_type": "image/png",
        "is_image": true,
        "image_width": 1280,
        "image_height": 585,
        "uploaded_at": "2020-11-17T12:16:10.035234+00:00"
    }

Filtres
-------

Filtre

Exemple

Exemple complet

equal

string

La valeur est 'string'

not\_equal

string

La valeur n'est pas 'string'

date\_is

UTC??today

La valeur est 'UTC??today'

date\_is\_not

UTC??today

La valeur n'est pas 'UTC??today'

date\_is\_before

UTC??today

La valeur est avant 'UTC??today'

date\_is\_on\_or\_before

UTC??today

La valeur est au plus tard 'UTC??today'

date\_is\_after

UTC??today

La valeur est après 'UTC??today'

date\_is\_on\_or\_after

UTC??today

La valeur est au plus tôt 'UTC??today'

date\_is\_within

UTC??today

La valeur est compris entre 'UTC??today'

date\_equal

obsolète

2020-01-01

La valeur est égal à '2020-01-01'

date\_not\_equal

obsolète

2020-01-01

La valeur est différent de '2020-01-01'

date\_equals\_today

obsolète

UTC

La valeur est aujourd'hui 'UTC'

date\_before\_today

obsolète

UTC

La valeur est avant aujourd'hui 'UTC'

date\_after\_today

obsolète

UTC

La valeur est après aujourd'hui 'UTC'

date\_within\_days

obsolète

Africa/Dakar?1

La valeur dans les X jours 'Africa/Dakar?1'

date\_within\_weeks

obsolète

Africa/Dakar?1

La valeur dans les X semaines 'Africa/Dakar?1'

date\_within\_months

obsolète

Africa/Dakar?1

La valeur dans les X mois 'Africa/Dakar?1'

date\_equals\_days\_ago

obsolète

Africa/Dakar?1

La valeur il y a X jours 'Africa/Dakar?1'

date\_equals\_months\_ago

obsolète

Africa/Dakar?1

La valeur il y a X mois 'Africa/Dakar?1'

date\_equals\_years\_ago

obsolète

Africa/Dakar?1

La valeur il y a X ans 'Africa/Dakar?1'

date\_equals\_week

obsolète

UTC

La valeur cette semaine 'UTC'

date\_equals\_month

obsolète

UTC

La valeur est ce mois-ci 'UTC'

date\_equals\_year

obsolète

UTC

La valeur est cette année 'UTC'

date\_equals\_day\_of\_month

1

La valeur est jour du mois '1'

date\_before

obsolète

2020-01-01

La valeur est avant '2020-01-01'

date\_before\_or\_equal

obsolète

2020-01-01

La valeur antérieure ou identique à la date '2020-01-01'

date\_after

obsolète

2020-01-01

La valeur est après '2020-01-01'

date\_after\_or\_equal

obsolète

2020-01-01

La valeur postérieur ou identique à la date '2020-01-01'

date\_after\_days\_ago

obsolète

20

La valeur Après X jours '20'

has\_empty\_value

string

La valeur a une valeur vide 'string'

has\_not\_empty\_value

string

La valeur n'a pas de valeur vide 'string'

has\_value\_equal

string

La valeur a une valeur égale à 'string'

has\_not\_value\_equal

string

La valeur n'a pas de valeur égale à 'string'

has\_value\_contains

string

La valeur a une valeur contenant 'string'

has\_not\_value\_contains

string

La valeur n'a pas de valeur contenant 'string'

has\_value\_contains\_word

string

La valeur a une valeur contenant le mot 'string'

has\_not\_value\_contains\_word

string

La valeur n'a pas de valeur contenant le mot 'string'

has\_value\_length\_is\_lower\_than

string

La valeur a une longueur de valeur inférieure à 'string'

contains

string

La valeur contient 'string'

contains\_not

string

La valeur ne contient pas 'string'

contains\_word

string

La valeur contient le mot 'string'

doesnt\_contain\_word

string

La valeur ne contient pas le mot 'string'

filename\_contains

string

La valeur nom du fichier contient 'string'

has\_file\_type

image | document

La valeur est de type 'image | document'

files\_lower\_than

2

La valeur Nb fichiers plus petit que '2'

length\_is\_lower\_than

5

La valeur a une longueur inférieure à '5'

higher\_than

100

La valeur est plus grand que '100'

higher\_than\_or\_equal

100

La valeur supérieur ou égal '100'

lower\_than

100

La valeur est plus petit que '100'

lower\_than\_or\_equal

100

La valeur inférieur ou égal '100'

is\_even\_and\_whole

true

La valeur Est un entier pair 'true'

single\_select\_equal

1

La valeur est '1'

single\_select\_not\_equal

1

La valeur n'est pas '1'

single\_select\_is\_any\_of

1,2

La valeur est l'une des valeurs '1,2'

single\_select\_is\_none\_of

1,2

La valeur n'est aucune des valeurs '1,2'

boolean

true

La valeur est 'true'

link\_row\_has

1

La valeur a '1'

link\_row\_has\_not

1

La valeur n'a pas '1'

link\_row\_contains

string

La valeur contient 'string'

link\_row\_not\_contains

string

La valeur ne contient pas 'string'

multiple\_select\_has

1

La valeur a '1'

multiple\_select\_has\_not

1

La valeur n'a pas '1'

multiple\_collaborators\_has

1

La valeur a '1'

multiple\_collaborators\_has\_not

1

La valeur n'a pas '1'

empty

La valeur est vide

not\_empty

La valeur n'est pas vide

user\_is

1

La valeur est '1'

user\_is\_not

1

La valeur n'est pas '1'

Erreurs HTTP
------------

Code

Nom

Description

200

Ok

La requête a été executée avec succès.

400

Bad request

La requête contient des valeurs invalides ou le contenu JSON n'a pas pu être décodé.

401

Unauthorized

Le jeton d'authentification utilisé est invalide.

404

Not found

La ligne ou la table n'a pas été trouvée.

413

Request Entity Too Large

La taille du contenu de la requête dépasse la taille maximale autorisée.

500

Internal Server Error

Le serveur a rencontré une erreur interne inatendue.

502

Bad gateway

Baserow est en cours de démarrage ou une interruption du service est en cours.

503

Service unavailable

Le serveur n'a pas répondu dans les délais impartis.

Example de requête





cURL

*   cURL
    
*   HTTP
    
*   JavaScript (axios)
    
*   Python (requests)
    

Nom des champs utilisateur

    curl \
    -H "Authorization: Token YOUR_DATABASE_TOKEN" \
    "https://sdbaserow.3xperts.tech"

Example de réponse





    {
        "error": "ERROR_NO_PERMISSION_TO_TABLE",
        "description": "The token does not have permissions to the table."
    }