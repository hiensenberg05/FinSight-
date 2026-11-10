import React from 'react';

interface PremiumCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const PremiumCard: React.FC<PremiumCardProps> = ({
  children,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`rounded-2xl glass-card-3d glass-card-3d-interactive transition-all duration-300 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
