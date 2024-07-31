************ LOST AND FOUND **********************

Step 1 : install python and mongodb first
Step 2 : setup virtual enviroment and then do all the steps....
Step 2 : install libraries from requirements.txt
Step 3 : Create database named = "Lost_And_Found"

Note : automatically when u run the app and insert data in app all collections and documenet u can see but u can always create it manually
      and insert one dummy record.......... as mongo is no sql we schema is flexible so no worries
      ex :        {
                         "DummyName": "DummyName",
                         "DummyId": "DummyId"
                    }

Step 4 : Create collections now : users,history,mcq_solved_verified

Step 5 : we have two sides --
        -user : task - loster,founder
        -admin : track : loster,founder,and also have data of how much items are recovered

Step 6 : admin user : username must be : admin123 and pass : 123 this is constraint then only recovered items are visible 

