import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
const CheckToken = () => {
  const navigate = useNavigate();

  useEffect(() => {
    console.log('REACT_APP_SKIP_TOKEN_CHECK:', process.env.REACT_APP_SKIP_TOKEN_CHECK);
    if (process.env.REACT_APP_SKIP_TOKEN_CHECK === "true") {
      console.log("Skipping token check in testing environment.");
      return;
    }
    const token = localStorage.getItem('token');
    
    if (token != null) {
      try {
        const decodedToken = jwtDecode(token);
        let currentDate = new Date();
        
        if (decodedToken.exp && decodedToken.exp * 1000 < currentDate.getTime()) {
          console.log("Token expired.");
          navigate("/login"); 
        } else {
          console.log("Valid token");
        }
      } catch (error) {
        console.error("Invalid token:", error);
        navigate("/login"); 
      }
    } else {
      navigate("/login");
    }
  }, [navigate]);
};

export default CheckToken;
