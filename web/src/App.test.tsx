import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App Shell", () => {
  it("renders without blank screen", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "严欣浩轻量 Web 展示层" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/FE-B1 Frontend Foundation/)).toBeInTheDocument();
  });
});