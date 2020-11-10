@client.command(pass_context=True)
@commands.is_owner()
async def addEmoji(ctx,id,hidden=True):
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()
        sql_insert_query = """ INSERT INTO emoji (name, id, animated, usage) VALUES (%s,%s,%s,%s)"""
        emoji = client.get_emoji(int(id))
        
        emojiData = (emoji.name,emoji.id,emoji.animated,0)
        try:
                cursor.execute(sql_insert_query, emojiData)
                #await ctx.send("Emoji added.")
                cursor.execute("SELECT * FROM emoji WHERE id = %s", (str(id),))
                await ctx.send(cursor.fetchall())

        except:
                "Emoji addition failed."

        cursor.close()
        connection.close()

@client.command(pass_context=True)
@commands.is_owner()
async def createEmojiTable(ctx,hidden=True,description="Creates emoji table."):

        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        try:
    
                cursor = connection.cursor()
                
                create_table_query = '''CREATE TABLE emoji
                          (name VARCHAR(30),
                         id VARCHAR(30),
                         animated BOOLEAN,
                         usage INT); '''
                
                cursor.execute(create_table_query)
                connection.commit()
                print("Table created successfully in PostgreSQL ")

        except (Exception, psycopg2.DatabaseError) as error :
                print ("Error while creating PostgreSQL table", error)


        finally:
                #closing database connection.
                        if(connection):
                                cursor.close()
                                connection.close()
                                print("PostgreSQL connection is closed")
