import React, { useEffect, useState } from "react";
import axios from "axios";

function Posts() {
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:5000/posts")
      .then(res => setPosts(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h2>Posts</h2>
      {posts.map(post => (
        <div key={post._id}>{post.title}</div>
      ))}
    </div>
  );
}

export default Posts;