function Topbar({ activePage }) {
  return (
    <header className="topbar">

      <div className="breadcrumbs">
        Workspace <span>/</span> {activePage}
      </div>

      <div className="top-actions">
        <button className="icon-button">⌕</button>
        <button className="icon-button">?</button>
        <div className="top-avatar">T</div>
      </div>

    </header>
  );
}

export default Topbar;