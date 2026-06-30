import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import StatCard from './StatCard';
import { FolderOpen } from 'lucide-react';

describe('StatCard component', () => {
  it('renders title, value, subtitle and icon correctly', () => {
    render(
      <BrowserRouter>
        <StatCard
          title="Total Projects"
          value="42"
          subtitle="All submissions ever"
          icon={FolderOpen}
          color="blue"
        />
      </BrowserRouter>
    );

    expect(screen.getByText('Total Projects')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('All submissions ever')).toBeInTheDocument();
  });

  it('renders a Link when "to" prop is provided', () => {
    render(
      <BrowserRouter>
        <StatCard
          title="Navigable"
          value="1"
          subtitle="Click me"
          icon={FolderOpen}
          color="green"
          to="/projects"
        />
      </BrowserRouter>
    );
    
    const linkElement = screen.getByRole('link');
    expect(linkElement).toHaveAttribute('href', '/projects');
  });
});
