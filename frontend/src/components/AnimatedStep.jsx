import React, { useState, useEffect } from 'react';

const AnimatedStep = ({ children, stepNumber, isVisible }) => {
  const [animationClass, setAnimationClass] = useState('');

  useEffect(() => {
    if (isVisible) {
      setAnimationClass('animate-fade-in-up');
    } else {
      setAnimationClass('animate-fade-out');
    }
  }, [isVisible]);

  return (
    <div className={`transition-all duration-500 ${animationClass}`}>
      {children}
    </div>
  );
};

// Dodaj style CSS dla animacji
const animationStyles = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes fadeOut {
    from {
      opacity: 1;
      transform: translateY(0);
    }
    to {
      opacity: 0;
      transform: translateY(-20px);
    }
  }

  .animate-fade-in-up {
    animation: fadeInUp 0.6s ease-out forwards;
  }

  .animate-fade-out {
    animation: fadeOut 0.3s ease-in forwards;
  }

  .animate-fade-in {
    animation: fadeInUp 0.4s ease-out forwards;
  }
`;

// Dodaj style do head dokumentu
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = animationStyles;
  document.head.appendChild(styleSheet);
}

export default AnimatedStep;
