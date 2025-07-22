import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!loginData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(loginData.email)) {
      newErrors.email = 'Invalid email format';
    }
    if (!loginData.password.trim()) {
      newErrors.password = 'Password is required';
    }
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    try {
      const res = await axios.post('http://localhost:8080/api/auth/login', loginData);
      alert(res.data);
      if (res.data === 'Login successful') {
        localStorage.setItem('loginSuccess', true);
        navigate('/');
      }
    } catch (err) {
      console.error(err);
      alert('Login failed');
    }
  };

  const handleChange = (e) => {
    setLoginData({ ...loginData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  return (
    <div className="form-container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input name="email" placeholder="Email" onChange={handleChange} />
        {errors.email && <p className="error">{errors.email}</p>}

        <input type="password" name="password" placeholder="Password" onChange={handleChange} />
        {errors.password && <p className="error">{errors.password}</p>}

        <button type="submit" className="btn">Login</button>
      </form>
      <p>New user? <Link to="/register">Register here</Link></p>
    </div>
  );
};

export default Login;
