import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Register.css';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '', email: '', password: '', firstName: '', lastName: '', phone: '', address: ''
  });

  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};

    if (!formData.firstName.trim()) newErrors.firstName = 'First name is required';
    if (!formData.lastName.trim()) newErrors.lastName = 'Last name is required';
    if (!formData.username.trim()) newErrors.username = 'Username is required';
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Invalid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
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
  const res = await axios.post('http://localhost:8080/api/auth/register', formData);
  alert(res.data);

  if (res.data.includes('success')) {
    navigate('/login');
  }
} catch (err) {
  if (err.response && err.response.data) {
    const errors = err.response.data;
    let message = '';

    for (const field in errors) {
      message += `${field}: ${errors[field]}\n`;
    }

    alert(message);
  } else {
    alert('Registration failed');
  }
}

  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' }); // clear error on change
  };

  return (
    <div className="form-container">
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <input name="firstName" placeholder="First Name" onChange={handleChange} />
        {errors.firstName && <p className="error">{errors.firstName}</p>}

        <input name="lastName" placeholder="Last Name" onChange={handleChange} />
        {errors.lastName && <p className="error">{errors.lastName}</p>}

        <input name="phone" placeholder="Phone" onChange={handleChange} />
        <input name="address" placeholder="Address" onChange={handleChange} />

        <input name="username" placeholder="Username" onChange={handleChange} />
        {errors.username && <p className="error">{errors.username}</p>}

        <input name="email" placeholder="Email" onChange={handleChange} />
        {errors.email && <p className="error">{errors.email}</p>}

        <input type="password" name="password" placeholder="Password" onChange={handleChange} />
        {errors.password && <p className="error">{errors.password}</p>}

        <button type="submit" className="btn">Register</button>
      </form>
    </div>
  );
};

export default Register;
