import mongodb from "mongodb";


const { MongoClient } = mongodb;

const uri = 'mongodb://127.0.0.1:27017/ModelData'
const client = new MongoClient(uri);

MongoClient.connect(url, function(err, db) {
  if (err) throw err;
  let dbo = db.db("ModelData");
  let query = { forecast_time: fh };
  dbo.collection("customers").find(query).toArray(function(err, result) {
    if (err) throw err;
    console.log(result);
    db.close();
  });
}); 